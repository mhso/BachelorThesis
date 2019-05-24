from PIL import Image

p = Image.open("../resources/gfx/pcs_wh.png")
s = Image.open("../resources/gfx/selected_piece.png")

blended = Image.alpha_composite(p, s)
blended.save("../resources/gfx/diswork.png")
