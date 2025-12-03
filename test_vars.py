# comprehensive_test.py - Testing all parser features

# === CONFIG SECTION ===
base_rate = 10
bonus_factor = 1.5

# === CIRCULAR DEPENDENCY ===
# This is the cycle we want to find
x = (z * 2) + base_rate
y = (x / 3) + 5
z = (y * 10) - bonus_factor

# === TRANSITIVE DEPENDENCIES ===
# These depend on the cycle
sub_total = x + y + z
tax_rate = 0.07
tax_amount = sub_total * tax_rate
total = sub_total + tax_amount

# === INDEPENDENT CALCULATIONS ===
admin_fee = base_rate * 0.1
final_total = total + admin_fee

# === AUGMENTED ASSIGNMENTS ===
# Testing += and *= operators
counter = 0
counter += base_rate  # counter depends on counter and base_rate
multiplier = 1
multiplier *= bonus_factor  # multiplier depends on multiplier and bonus_factor
accumulator = total
accumulator += tax_amount  # accumulator depends on accumulator and tax_amount

# === TUPLE UNPACKING ===
# Testing multiple assignments
min_value, max_value = base_rate, total  # min_value depends on base_rate, max_value depends on total
rate_a, rate_b = tax_rate, bonus_factor  # rate_a depends on tax_rate, rate_b depends on bonus_factor
calc_x, calc_y = x + y, z * 2  # calc_x depends on x and y, calc_y depends on z

# === COMPLEX MIXED CASES ===
# Combining multiple features
result_a, result_b = counter + multiplier, accumulator
result_a += final_total  # result_a now also depends on itself and final_total

# === UNUSED / DEAD VARIABLE ===
temp = 100
