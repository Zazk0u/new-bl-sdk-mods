from __future__ import annotations  # Ensures type hints are ignored at runtime

from typing import TYPE_CHECKING

from unrealsdk import make_struct


if TYPE_CHECKING:
    from common import *


def Pointer(
        Dummy:int = 0, 
    ) -> Object.Pointer:
    return make_struct("Pointer", Dummy=Dummy)


def Vector(
        X:float = 0, 
        Y:float = 0, 
        Z:float = 0, 
    ) -> Object.Vector:
    return make_struct("Vector", X=X, Y=Y, Z=Z)


def BehaviorVariableValueUnion_Mirror(
        Data:Object.Pointer = Pointer(), 
    ) -> BehaviorProviderDefinition.BehaviorVariableValueUnion_Mirror:
    return make_struct("BehaviorVariableValueUnion_Mirror", Data=Data)


def BehaviorVariableData(
        Name:str = "", 
        Type:BehaviorProviderDefinition.EBehaviorVariableType = 0, 
        Value:BehaviorProviderDefinition.BehaviorVariableValueUnion_Mirror = BehaviorVariableValueUnion_Mirror(),
    ) -> BehaviorProviderDefinition.BehaviorVariableData:
    return make_struct("BehaviorVariableData", IntValue=Name, FloatValue=Type, VectorValue=Value)


def BehaviorVariableValue(
        IntValue:int = 0, 
        FloatValue:float = 0.00, 
        VectorValue:Object.Vector = Vector(),
        ObjectValue:Object = None,
        VariableType:BehaviorProviderDefinition.EBehaviorVariableType = 0
    ) -> BehaviorProviderDefinition.BehaviorVariableValue:
    return make_struct(
        "BehaviorVariableValue",
        IntValue=IntValue, 
        FloatValue=FloatValue, 
        VectorValue=VectorValue,
        ObjectValue=ObjectValue,
        VariableType=VariableType
    )


def BehaviorKernelInfo(
        StateForThreadRunningThisBehavior:Object.Pointer = Pointer(),
        WorldTime:float = 0, 
        ExecutionTime:float = 0,
        WorldDeltaTime:float = 0,
        ExecutionDelayError:float = 0,
        NextExecutionDelayTime:float = 0,
        bHasLinkedOutputs:bool = False,
        bIsInitialRunOfThisBehavior:bool = False,
    ) -> BehaviorBase.BehaviorKernelInfo:
    return make_struct(
        "BehaviorKernelInfo",
        StateForThreadRunningThisBehavior=StateForThreadRunningThisBehavior, 
        WorldTime=WorldTime, 
        ExecutionTime=ExecutionTime,
        WorldDeltaTime=WorldDeltaTime,
        ExecutionDelayError=ExecutionDelayError,
        NextExecutionDelayTime=NextExecutionDelayTime,
        bHasLinkedOutputs=bHasLinkedOutputs,
        bIsInitialRunOfThisBehavior=bIsInitialRunOfThisBehavior
    )