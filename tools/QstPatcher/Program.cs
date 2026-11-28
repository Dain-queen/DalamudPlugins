// Questionable.dll 패치 도구
//
// 문제: Questionable의 IPCUtils.IPCSubscriber.Version(name) 은
//       InstalledPlugins 에서 p.Name(표시 이름) == name 으로 플러그인을 찾는다.
//       vnavmesh CN 은 표시 이름이 "vnavmesh CN" 이라 못 찾고(null),
//       NavmeshIpc.IsReady() 가 항상 false → 캐릭터가 전혀 움직이지 않는다.
//
// 수정: 비교식을 (p.Name == name || p.InternalName == name) && p.IsLoaded 로 바꾼다.
//       원래 조건을 그대로 포함하므로 기존에 잡히던 플러그인은 똑같이 잡힌다.
//
// 사용: dotnet run --project tools/QstPatcher -- <입력 Questionable.dll> <출력 Questionable.dll>
using Mono.Cecil;
using Mono.Cecil.Cil;
using Mono.Cecil.Rocks;

if (args.Length != 2)
{
    Console.Error.WriteLine("사용법: QstPatcher <입력.dll> <출력.dll>");
    return 2;
}

var input = args[0];
var output = args[1];

// 저장할 때 참조 어셈블리(Dalamud, ECommons 등)를 찾아야 하므로 검색 경로를 넣는다.
// QST_REF_DIRS: 경로 목록(Path.PathSeparator 로 구분) — 플러그인 zip 압축 해제 폴더, Dalamud 배포본 폴더
var resolver = new DefaultAssemblyResolver();
resolver.AddSearchDirectory(Path.GetDirectoryName(Path.GetFullPath(input))!);
foreach (var dir in (Environment.GetEnvironmentVariable("QST_REF_DIRS") ?? "").Split(Path.PathSeparator, StringSplitOptions.RemoveEmptyEntries))
    foreach (var sub in Directory.EnumerateDirectories(dir, "*", SearchOption.AllDirectories).Prepend(dir))
        resolver.AddSearchDirectory(sub);

using var asm = AssemblyDefinition.ReadAssembly(input, new ReaderParameters { ReadSymbols = false, InMemory = true, AssemblyResolver = resolver });
var module = asm.MainModule;

static IEnumerable<TypeDefinition> AllTypes(IEnumerable<TypeDefinition> types)
{
    foreach (var t in types)
    {
        yield return t;
        foreach (var n in AllTypes(t.NestedTypes))
            yield return n;
    }
}

static bool IsPluginGetter(Instruction i, string name) =>
    (i.OpCode == OpCodes.Callvirt || i.OpCode == OpCodes.Call)
    && i.Operand is MethodReference m
    && m.Name == name
    && m.DeclaringType.Name == "IExposedPlugin";

static bool IsStringEquality(Instruction i) =>
    i.OpCode == OpCodes.Call
    && i.Operand is MethodReference m
    && m.Name == "op_Equality"
    && m.DeclaringType.FullName == "System.String";

int patched = 0;
foreach (var type in AllTypes(module.Types).Where(t => t.FullName.StartsWith("Questionable.External.IPCUtils", StringComparison.Ordinal)))
{
    foreach (var method in type.Methods.Where(m => m.HasBody))
    {
        var il = method.Body.Instructions;
        // 이미 패치됐는지 확인
        if (il.Any(i => IsPluginGetter(i, "get_InternalName")) && il.Any(i => IsPluginGetter(i, "get_Name")))
        {
            Console.WriteLine($"이미 패치됨: {type.FullName}::{method.Name}");
            patched++;
            continue;
        }

        for (int idx = 1; idx < il.Count; idx++)
        {
            var getName = il[idx];
            if (!IsPluginGetter(getName, "get_Name"))
                continue;

            // 기대 형태: <p 로드> callvirt get_Name <name 로드...> call op_Equality brfalse X
            int eqIdx = -1;
            for (int j = idx + 1; j < Math.Min(idx + 5, il.Count); j++)
                if (IsStringEquality(il[j])) { eqIdx = j; break; }
            if (eqIdx < 0 || eqIdx + 1 >= il.Count)
                continue;
            var branch = il[eqIdx + 1];
            if (branch.OpCode != OpCodes.Brfalse && branch.OpCode != OpCodes.Brfalse_S)
                continue;
            if (eqIdx + 2 >= il.Count)
                continue;

            var loadPlugin = il[idx - 1];
            var loadName = il.Skip(idx + 1).Take(eqIdx - idx - 1).ToList();
            var afterBranch = il[eqIdx + 2];

            var nameRef = (MethodReference)getName.Operand;
            var internalNameRef = new MethodReference("get_InternalName", nameRef.ReturnType, nameRef.DeclaringType)
            {
                HasThis = nameRef.HasThis,
                ExplicitThis = nameRef.ExplicitThis,
                CallingConvention = nameRef.CallingConvention,
            };
            internalNameRef = module.ImportReference(internalNameRef);

            var proc = method.Body.GetILProcessor();
            method.Body.SimplifyMacros();

            // op_Equality 직후: 표시 이름이 같으면 바로 IsLoaded 확인으로 건너뛴다
            var eq = il[eqIdx];
            var insert = new List<Instruction>
            {
                proc.Create(OpCodes.Brtrue, afterBranch),
                Clone(proc, loadPlugin),
                proc.Create(getName.OpCode, internalNameRef),
            };
            foreach (var ln in loadName)
                insert.Add(Clone(proc, ln));
            insert.Add(proc.Create(OpCodes.Call, (MethodReference)eq.Operand));

            var anchor = eq;
            foreach (var ins in insert)
            {
                proc.InsertAfter(anchor, ins);
                anchor = ins;
            }

            method.Body.OptimizeMacros();
            Console.WriteLine($"패치함: {type.FullName}::{method.Name}");
            foreach (var i in method.Body.Instructions)
                Console.WriteLine($"    {i}");
            patched++;
            break;
        }
    }
}

if (patched != 1)
{
    Console.Error.WriteLine($"!! 패치 대상이 정확히 1개여야 하는데 {patched}개를 찾음 — Questionable 코드가 바뀌었을 수 있음");
    return 1;
}

asm.Write(output);
Console.WriteLine($"저장: {output}");
return 0;

static Instruction Clone(ILProcessor proc, Instruction src) => src.Operand switch
{
    null => proc.Create(src.OpCode),
    FieldReference f => proc.Create(src.OpCode, f),
    MethodReference m => proc.Create(src.OpCode, m),
    TypeReference t => proc.Create(src.OpCode, t),
    ParameterDefinition p => proc.Create(src.OpCode, p),
    VariableDefinition v => proc.Create(src.OpCode, v),
    string s => proc.Create(src.OpCode, s),
    int n => proc.Create(src.OpCode, n),
    sbyte n => proc.Create(src.OpCode, n),
    _ => throw new InvalidOperationException($"복사할 수 없는 명령: {src}"),
};
