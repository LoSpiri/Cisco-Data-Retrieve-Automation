## creating functions to write the output word file
import pandas as pd


def get_paragraph(paras, text):
        """Return the paragraph where the text resides

        Args:
            paras(document.paragraphs): All the paragraphs in the document
            text (str): The text in the paragraph to match

        """
        for para in paras:
            if text in para.text:
                return para
        raise KeyError("The text cannot be found anywhere in the document")


def move_table_after(table, paragraph):
    tbl, p = table._tbl, paragraph._p
    p.addnext(tbl)

    # paragraph = paragraph_to_precede_new_table  # however you get this paragraph
    # table = document.add_table(...)
    # move_table_after(table, paragraph)


def print_table(table):
    for i in table.rows:
        for j in i.cells:
            print(j.text)

    
def df_to_table_at_position(document,general_df,position):
    table = document.add_table(general_df.shape[0]+1, general_df.shape[1])
    table.allow_autofit = True
    table.autofit = True
    table.style = 'Table Grid'
    
    for j in range(general_df.shape[-1]):
        table.cell(0,j).text = general_df.columns[j]

    for i in range(general_df.shape[0]):
        for j in range(general_df.shape[-1]):
            table.cell(i+1,j).text = str(general_df.values[i,j])

    paragraph = get_paragraph(document.paragraphs,position)

    move_table_after(table,paragraph)

    
def replace_text(paragraph,old_text, new_text):
    inline = paragraph.runs
    for i in range(len(inline)):
        if old_text in inline[i].text:
            text = inline[i].text.replace(old_text, new_text)
            inline[i].text = text


