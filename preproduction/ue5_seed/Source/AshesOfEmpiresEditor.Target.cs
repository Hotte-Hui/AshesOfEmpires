using UnrealBuildTool;
using System.Collections.Generic;

public class AshesOfEmpiresEditorTarget : TargetRules
{
    public AshesOfEmpiresEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V5;
        ExtraModuleNames.Add("AshesOfEmpires");
    }
}
