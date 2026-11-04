#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "AshesSaveGame.generated.h"

UCLASS(BlueprintType)
class ASHESOFEMPIRES_API UAshesSaveGame : public USaveGame
{
    GENERATED_BODY()
public:
    UPROPERTY(SaveGame, BlueprintReadWrite, Category="Story") int32 SaveVersion = 2;
    UPROPERTY(SaveGame, BlueprintReadWrite, Category="Story") TMap<FName, int32> IntegerFlags;
    UPROPERTY(SaveGame, BlueprintReadWrite, Category="Story") TMap<FName, bool> BooleanFlags;
    UPROPERTY(SaveGame, BlueprintReadWrite, Category="Story") TArray<FName> CompletedObjectives;
    UPROPERTY(SaveGame, BlueprintReadWrite, Category="Story") TArray<FName> CompletedEvents;
    UPROPERTY(SaveGame, BlueprintReadWrite, Category="Story") TArray<FName> Inventory;
    UPROPERTY(SaveGame, BlueprintReadWrite, Category="Story") FName CurrentScene = TEXT("L_A1_Railyard");
    UPROPERTY(SaveGame, BlueprintReadWrite, Category="Story") FName ActiveCharacter = TEXT("alexei");
};
