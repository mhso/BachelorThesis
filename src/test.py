step = 1000
max_step = 600
term_val = 1

if step < max_step:
    ratio = step / max_step
    z_val = term_val * (1 - ratio)
    q_val = 0.1 * ratio
    target_val = z_val + q_val
else:
    target_val = 0.1
print(target_val)
