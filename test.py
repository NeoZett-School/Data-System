from Data import Data, data_factory, is_data_factory, make_data_factory, field

@data_factory
class Foo:
    x: int = field(default=1)

    def say_x(self) -> None:
        print(self.x)

class Bar(Foo, include_methods=True):
    y: int = 2

b = Bar()
b.x += 5
b.say_x()