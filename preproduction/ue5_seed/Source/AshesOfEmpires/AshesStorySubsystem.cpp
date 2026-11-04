#include "AshesStorySubsystem.h"
#include "AshesSaveGame.h"
#include "Kismet/GameplayStatics.h"

void UAshesStorySubsystem::NewStory()
{
    IntegerFlags.Empty(); BooleanFlags.Empty(); CompletedObjectives.Empty(); CompletedEvents.Empty(); Inventory.Empty();
    IntegerFlags.Add(TEXT("irina_trust"), 0);
    IntegerFlags.Add(TEXT("alexei_secrecy"), 0);
    IntegerFlags.Add(TEXT("matthias_evidence"), 0);
    IntegerFlags.Add(TEXT("office_suspicion"), 0);
    IntegerFlags.Add(TEXT("civilian_welfare"), 0);
    BooleanFlags.Add(TEXT("c17_confirmed"), false);
    BooleanFlags.Add(TEXT("signal_restored"), false);
    BooleanFlags.Add(TEXT("blueprint_match_confirmed"), false);
    BooleanFlags.Add(TEXT("slice_finished"), false);
    CurrentScene = TEXT("L_A1_Railyard");
    ActiveCharacter = TEXT("alexei");
}

bool UAshesStorySubsystem::HasCompletedObjective(FName ObjectiveId) const
{
    return CompletedObjectives.Contains(ObjectiveId);
}

bool UAshesStorySubsystem::MarkObjectiveOnce(FName ObjectiveId)
{
    // IMPORTANT: this illustrative method does not check JSON prerequisites.
    // Do not expose it directly to production interactables without authoritative quest validation.
    if (ObjectiveId.IsNone() || CompletedObjectives.Contains(ObjectiveId)) { return false; }
    CompletedObjectives.Add(ObjectiveId);
    return true;
}

bool UAshesStorySubsystem::SaveStory(const FString& SlotName)
{
    if (SlotName.IsEmpty()) { return false; }
    UAshesSaveGame* Save = Cast<UAshesSaveGame>(UGameplayStatics::CreateSaveGameObject(UAshesSaveGame::StaticClass()));
    if (!Save) { return false; }
    Save->IntegerFlags = IntegerFlags;
    Save->BooleanFlags = BooleanFlags;
    Save->CompletedObjectives = CompletedObjectives;
    Save->CompletedEvents = CompletedEvents;
    Save->Inventory = Inventory;
    Save->CurrentScene = CurrentScene;
    Save->ActiveCharacter = ActiveCharacter;
    return UGameplayStatics::SaveGameToSlot(Save, SlotName, 0);
}

bool UAshesStorySubsystem::LoadStory(const FString& SlotName)
{
    if (SlotName.IsEmpty()) { return false; }
    UAshesSaveGame* Save = Cast<UAshesSaveGame>(UGameplayStatics::LoadGameFromSlot(SlotName, 0));
    if (!Save || Save->SaveVersion != 2) { return false; } // TODO: Save migration using verified data defs.
    IntegerFlags = Save->IntegerFlags;
    BooleanFlags = Save->BooleanFlags;
    CompletedObjectives = Save->CompletedObjectives;
    CompletedEvents = Save->CompletedEvents;
    Inventory = Save->Inventory;
    CurrentScene = Save->CurrentScene;
    ActiveCharacter = Save->ActiveCharacter;
    return true;
}
