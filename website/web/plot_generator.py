import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from flask import current_app
from .llm_client import request_llm


def build_plot_generation_prompt(user_prompt: str, df_preview: pd.DataFrame) -> str:
    """
    Creates a detailed, structured prompt for the LLM to generate Python code for a plot.
    --- V2: Now includes a clear, correct example to guide the LLM. ---
    """
    prompt_lines = [
        "You are an expert Python data visualization assistant. Your task is to generate clean, executable Python code to create a plot using the pandas and matplotlib libraries.",
        "The code must adhere to the following strict rules:",
        "1. Assume a pandas DataFrame named 'df' is already loaded in memory.",
        "2. The code must NOT include any data loading or sample data creation (e.g., no `pd.read_csv` or `pd.DataFrame({...})`).",
        "3. The final line of code MUST save the plot to a BytesIO buffer. The buffer variable must be named `buffer`.",
        "4. The code should not call `plt.show()`.",
        "---",
        "**User Request:**",
        f'"{user_prompt}"',
        "",
        "**Data Sample (first 5 rows of the DataFrame 'df'):**",
        df_preview.to_string(),
        "",
        "---",
        "**PERFECT CODE EXAMPLE:**",
        "```python",
        "plt.figure(figsize=(10, 6))",
        "plt.bar(df['City'], df['Sales'])",
        "plt.xlabel('City')",
        "plt.ylabel('Total Sales')",
        "plt.title('Total Sales by City')",
        "plt.xticks(rotation=45)",
        "plt.tight_layout()",
        "buffer = io.BytesIO()",
        "plt.savefig(buffer, format='png')",
        "buffer.seek(0)",
        "```",
        "---",
        "**Your Python Code (Do not include the ```python ... ``` fences in your response):**"
    ]
    return "\n".join(prompt_lines)


def generate_plot_image(file_id: str, user_prompt: str) -> str:
    """
    Generates a plot image by querying the LLM for Python code and executing it.
    """
    # 1. Fetch the file and create a DataFrame from its preview
    file_obj = current_app.db.get_file(file_id)
    if not file_obj or not file_obj.preview:
        raise ValueError("File not found or has no data preview.")

    df = pd.DataFrame(file_obj.preview)

    # 2. Build the prompt for the LLM
    prompt = build_plot_generation_prompt(user_prompt, df.head())

    # 3. Request the Python code from the LLM
    code_lines = request_llm(prompt)
    if not code_lines:
        raise RuntimeError("LLM did not return any code.")

    # The llm_client now cleans the response, but we join it into a single string here.
    python_code = "\n".join(code_lines)

    # 4. Execute the code to generate the plot
    try:
        local_scope = {'df': df, 'plt': plt, 'io': io, 'base64': base64}
        exec(python_code, globals(), local_scope)

        if 'buffer' not in local_scope or not isinstance(local_scope['buffer'], io.BytesIO):
            raise ValueError("The generated code did not produce the expected plot buffer.")

        # 5. Convert the plot image to a base64 string
        img_bytes = local_scope['buffer'].getvalue()
        base64_img = base64.b64encode(img_bytes).decode('utf-8')

        return f"data:image/png;base64,{base64_img}"

    except Exception as e:
        # Include the generated code in the error for easier debugging
        error_message = f"An error occurred while executing the generated plot code: {e}\n--- Generated Code ---\n{python_code}"
        raise RuntimeError(error_message)