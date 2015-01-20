__author__ = 'raek'


from enum import Enum

class Animals(Enum):
    ant = 1
    bee = 2
    cat = 3
    dog = 4

print(repr(Animals.dog))
print(Animals.dog.name)
print(Animals.dog.value)

number = Animals.dog.value
print(number)

print(Animals(1))

oneAnimal = Animals.cat
print oneAnimal.value

