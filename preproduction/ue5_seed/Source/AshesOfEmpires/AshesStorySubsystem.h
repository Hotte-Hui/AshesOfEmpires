#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "AshesStorySubsystem.generated.h"

/** Minimal example only. Real v3 prereq checks and story data import are not implemented. */
UCLASS(BlueprintType)
class ASHESOFEMPIRES_API UAshesStorySubsystem : public UGameInstanceSubsystem
{
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category="Story") void NewStory();
    UFUNCTION(BlueprintCallable, Category="Story") bool SaveStory(const FString& SlotName);
    UFUNCTION(BlueprintCallable, Category="Story") bool LoadStory(const FString& SlotName);
    UFUNCTION(BlueprintPure, Category="Story") bool HasCompletedObjective(FName ObjectiveId) const;
    UFUNCTION(BlueprintCallable, Category="Story") bool MarkObjectiveOnce(FName ObjectiveId);
    UFUNCTION(BlueprintPure, Category="Story") FName GetCurrentScene() const { return CurrentScene; }

    // TODO: Replace all hardcoded defaults with verified v3 DataAsset imports.
    UPROPERTY(BlueprintReadOnly, Category="Story") TMap<FName,int32> IntegerFlags;
    UPROPERTY(BlueprintReadOnly, Category="Story") TMap<FName,bool> BooleanFlags;
    UPROPERTY(BlueprintReadOnly, Category="Story") TArray<FName> CompletedObjectives;
    UPROPERTY(BlueprintReadOnly, Category="Story") TArray<FName> CompletedEvents;
    UPROPERTY(BlueprintReadOnly, Category="Story") TArray<FName> Inventory;
    UPROPERTY(BlueprintReadOnly, Category="Story") FName CurrentScene = TEXT("L_A1_Railyard");
    UPROPERTY(BlueprintReadOnly, Category="Story") FName ActiveCharacter = TEXT("alexei");
};
