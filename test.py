from Data import Data, data_factory, is_data_factory, make_data_factory

@data_factory(frozen=False, include_methods=True, config={"Hello": {"version": 1.0}})
class Hello:
    age: int
    hello: str = "Hello"
    
    def say_hi_jupiter(self) -> None:
        print(f"{self.hello}, Jupiter!")

h = Hello(age=25, frozen=True)
h.age += 1000
print(h.get("age", 0))
h.say_hi_jupiter()
print(is_data_factory(h))
print(make_data_factory(Hello, age=25))