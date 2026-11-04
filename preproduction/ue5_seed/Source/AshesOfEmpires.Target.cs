using UnrealBuildTool;
using System.Collections.Generic;

public class AshesOfEmpiresTarget : TargetRules
{
    public AshesOfEmpiresTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Game;
        DefaultBuildSettings = BuildSettingsVersion.V5;
        ExtraModuleNames.Add("AshesOfEmpires");
    }
}
