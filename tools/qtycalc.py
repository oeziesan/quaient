# main parameter
# for cross margin
import math

print("use international std. (use '.' instead of ',')")
B = float(input("balance: "))
R = float(input("risk (%): "))/100
Pe = float(input("entry price: "))
Ps = float(input("sl price: "))
delta_P = abs(Pe-Ps)

Q = (B*R)/delta_P #qty
N = Q*Pe
Lsafe = math.floor(1.5*(N/B)) #safe leverage (x1.5 tolerating the fee n slippage)

print("qty:", f"{Q:.4f}","in pair (not usdt)")
print("safe leverage:", Lsafe,"x")