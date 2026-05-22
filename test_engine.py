from engine import DiffusionEngine
import torch

def test_engine():
    print("--- Start testu silnika ---")
    
    # 1. Sprawdzenie CUDA
    if not torch.cuda.is_available():
        print("BŁĄD: CUDA nie jest dostępna!")
        return

    # 2. Inicjalizacja silnika
    try:
        engine = DiffusionEngine()
        print("Silnik zainicjalizowany poprawnie.")
    except Exception as e:
        print(f"Błąd inicjalizacji silnika: {e}")
        return

    # 3. Próba generowania (bardzo szybki test)
    print("Rozpoczynam próbne generowanie...")
    try:
        file, _ = engine.generate(
            prompt="a small toy robot",
            neg_prompt="blur",
            cfg=7.0,
            steps=5, # Bardzo mało kroków dla szybkiego testu
            width=256, # Mały rozmiar dla szybkości
            height=256
        )
        print(f"Test zakończony sukcesem! Obraz zapisano jako: {file}")
    except Exception as e:
        print(f"Błąd podczas generowania: {e}")

if __name__ == "__main__":
    test_engine()