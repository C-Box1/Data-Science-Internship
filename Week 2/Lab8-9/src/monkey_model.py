from utils import check_hexacolor

class Monkey:
	"""A monkey."""
	def __init__(self, weight: float, size: float, fur_color: str, species: str = ""):
		if not isinstance(weight, (int, float)):
			raise ValueError(f"Weight must be a number, got {type(weight)}")
		if not isinstance(size, (int, float)):
			raise ValueError(f"Size must be a number, got {type(size)}")
		if size <= 0:
			raise ValueError(f"Size must be positive, got {size}")
		if weight <=0:
			raise ValueError(f"Weight must be positive, got {weight}")
		if not check_hexacolor(fur_color):
			raise ValueError(f"Invalid fur color : {fur_color}")
		self.size = size
		self.weight = weight
		self.fur_color = fur_color
		self.species = species

	def __str__(self):
		return f"Monkey ({self.species}), {self.weight}kg, {self.size}cm, fur: {self.fur_color}"
	
	def __repr__(self):
		return self.__str__()
	
	@property
	def bmi(self) -> float:
		"""Compute the monkey's Body Mass Index (BMI)."""
		return self.weight / (self.size ** 2)