
class contributor:
    def __init__(self, name, index):
        self.name = name
        self.index = index
        
    def __str__(self) -> str:
        return self.name
        
    def __repr__(self) -> str:
        return self.name


CONTRIBUTORS = [ 
    contributor("Quentin", 5), contributor("Gary", 6),
    contributor("20100", 7), contributor("Romain", 8),
    contributor("Samuel", 9), contributor("Galtier", 10), 
    contributor("Roxane", 11), contributor("Clémence", 12), 
    contributor("Lucas", 13)
]

if __name__ == "__main__":
    print("Ach! Musik contributors are: {}".format(CONTRIBUTORS))