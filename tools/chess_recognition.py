from transformers import DetrImageProcessor, DetrForObjectDetection
from PIL import Image
from pathlib import Path
import torch
from langchain_core.tools import tool


processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")

label_map = {
    0: "P", 1: "N", 2: "B", 3: "R", 4: "Q", 5: "K",  # белые
    6: "p", 7: "n", 8: "b", 9: "r", 10: "q", 11: "k"  # чёрные
}

@tool
def chess_board_recognition(image_path: str) -> str:
    """
    Recognizes a chessboard from an image and returns the position in FEN format.
    """
    try:
        path = Path(image_path)
        image = Image.open(path).convert("RGB")
        width, height = image.size

        inputs = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)

        target_sizes = torch.tensor([[height, width]])
        results = processor.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=0.9
        )[0]

        cell_w = width / 8
        cell_h = height / 8

        board = [["" for _ in range(8)] for _ in range(8)]

        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            piece = label_map.get(label.item(), "?")
            x_center = (box[0] + box[2]) / 2
            y_center = (box[1] + box[3]) / 2

            col = int(x_center.item() // cell_w)
            row = int(y_center.item() // cell_h)

            if 0 <= row < 8 and 0 <= col < 8:
                board[row][col] = piece

        # FEN format
        fen_rows = []
        for row in board:
            fen_row = ""
            empty = 0
            for cell in row:
                if cell == "":
                    empty += 1
                else:
                    if empty:
                        fen_row += str(empty)
                        empty = 0
                    fen_row += cell
            if empty:
                fen_row += str(empty)
            fen_rows.append(fen_row)

        fen_position = "/".join(fen_rows)
        return f"Recognitional result, use it for algebraic format answer: {fen_position} w - - 0 1"

    except Exception as e:
        return f"I can't recognize (chess recognition error: {e})"