from abc import ABC, abstractmethod

class Base(ABC):

    @abstractmethod
    def foo(self, x: int) -> bool:
        pass
    
    @property
    @abstractmethod
    def y(self) -> str:
        pass

    def test(self) -> None:
        print(1)

class Derived(Base):
    def __init__(self, y_value: str):
        self._y = y_value
    
    def foo(self, x: int) -> bool:
        return x > 0  # Example implementation for foo method
    
    @property
    def y(self) -> str:
        return self._y

    @y.setter
    def y(self, value: str) -> None:
        self._y = value
    


# Example usage
derived_obj = Derived("example")
print(derived_obj.foo(5))  # Output: True
print(derived_obj.y)       # Output: example
derived_obj.test()