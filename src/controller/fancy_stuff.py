import matplotlib.pyplot as plt
from glob import glob
from PIL import ImageGrab, ImageFont, ImageDraw

class FancyDraw:
    prev_confidence = "NA"
    prev_duration = 0

    @staticmethod
    def save_fancy_stuff(gui, duration, confidence, agent):
        x = gui.root.winfo_rootx()+gui.canvas.winfo_x()
        y = gui.root.winfo_rooty()+gui.canvas.winfo_y()
        x1 = x+gui.canvas.winfo_width()
        y1 = y+gui.canvas.winfo_height()
        img = ImageGrab.grab().crop((x, y, x1+350, y1))

        draw = ImageDraw.Draw(img)
        w, h = img.size
        draw.rectangle((w-350, 0, w, y1), fill=(0, 0, 0, 255))
        draw.rectangle((0, gui.canvas.winfo_height(), w, h), fill=(0, 0, 0, 255))

        fnt = ImageFont.truetype("../resources/Verdana.ttf", 28)
        fnt_bold = ImageFont.truetype("../resources/Verdana_Bold.ttf", 28)

        confidence_kata = confidence
        duration_kata = duration
        confidence_mcts = FancyDraw.prev_confidence
        duration_mcts = FancyDraw.prev_duration
        if agent != "MCTS":
            confidence_kata, confidence_mcts = confidence_mcts, confidence_kata
            duration_kata, duration_mcts = duration_mcts, duration_kata

        text_x = gui.canvas.winfo_width()+30
        text_y = 50

        draw.text((text_x+70, text_y+30), "Katafanga", font=fnt_bold, fill=(255, 255, 255, 255))
        draw.text((text_x, text_y+70), "Simulations: 200", font=fnt, fill=(255, 255, 255, 255))
        draw.text((text_x, text_y+105), f"Confidence: {confidence_kata}", font=fnt, fill=(255, 255, 255, 255))
        draw.text((text_x, text_y+140), f"Turn duration: {duration_kata} s", font=fnt, fill=(255, 255, 255, 255))

        draw.text((text_x+105, text_y+205), "MCTS", font=fnt_bold, fill=(255, 255, 255, 255))
        draw.text((text_x, text_y+245), "Simulations: 10000", font=fnt, fill=(255, 255, 255, 255))
        draw.text((text_x, text_y+280), f"Confidence: {confidence_mcts}", font=fnt, fill=(255, 255, 255, 255))
        draw.text((text_x, text_y+320), f"Turn duration: {duration_mcts} s", font=fnt, fill=(255, 255, 255, 255))

        path = "../resources/video_stuff/"
        file_num = len(glob(f"{path}*.png"))+1
        FancyDraw.prev_confidence = confidence
        FancyDraw.prev_duration = duration

        img.save(f"{path}{file_num}.png")
