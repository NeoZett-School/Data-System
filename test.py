from Data import Data, data_factory, is_data_factory, make_data_factory, field, computed_field, pretty_repr, inspect_data

@data_factory(include_methods=True)
class Date:
    year: int = 2025
    month: int = 10
    day: int = field(required=True)
    year_month_day: str = computed_field(lambda self: f"{self.year} - {self.month} - {self.day}")

    #@computed_field
    #def year_month(self): ... 
    # Works. But this will show as a function.

today = Date(day=31) # Day is required, or you'll get an error.
print(today.content)