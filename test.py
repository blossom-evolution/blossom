class A(object):
     def __init__(self, a):
             self.a = a
     def b(self, x):
             print(self.a, x)
     def c(self):
             another = A(10)
             print(self.a, 'hello')
     def d(self):
             another = A(10)
             print(getattr(A, 'b')(another, 'hello2'))
