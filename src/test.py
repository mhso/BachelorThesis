hashes = [str(p) for p in pieces]
hashes.reverse()
evens = []
for i in range(0, len(hashes), 2):
    h = hashes[i]
    unique = False
    for other_h in evens:
        if other_h != h:
            unique = True
            break
    if unique:
        break
    evens.append(i)
odds = []
for i in range(1, len(hashes), 2):
    h = hashes[i]
    unique = False
    for other_h in odds:
        if other_h != h:
            unique = True
            break
    if unique:
        break
    odds.append(i)
new_l = []
iters = min((len(evens), len(odds)))
if len(evens) != len(odds):
    iters += 1
for i in range(iters):
    if i < len(evens):
        new_l.append(pieces[evens[i]])
    if i < len(odds):
        new_l.append(pieces[odds[i]])
return new_l