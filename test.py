from Data import Data, data_factory, is_data_factory, make_data_factory, field, computed_field

@data_factory
class Foo:
    x: int = field(default=1)

    def say_x(self) -> None:
        print(self.x)

    x_hello = computed_field(lambda self: f"{self.x} hello")

    #@computed_field
    #def x_hello(self):
    #    return f"{self.x} hello"

class Bar(Foo, include_methods=True):
    y: int = 2

b = Bar()
b.x += 5
b.say_x()
print(b.x_hello)