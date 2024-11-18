from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import re
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def filter_by_branch(df, branch):
    return df[df['Action'].str.contains(branch, case=False, na=False)]

def sum_unique_visits(data):
    numbers_in_parentheses = re.findall(r'\((\d+)\)', " ".join(data))
    return sum(map(int, numbers_in_parentheses))

def summarize_by_branch(df_branch):
    df_copy = df_branch.copy()
    for idx, row in df_copy.iterrows():
        if row['Unique transitions'] > row['Received by SMS provider']:
            df_copy.at[idx, 'Unique transitions'] = sum_unique_visits([row['Unique visits ?']])
    summary = df_copy[['Received by SMS provider', 'Delivered', 'Unique transitions']].sum()
    summary['Unique visits ?'] = sum_unique_visits(df_copy['Unique visits ?'])
    return summary.to_dict()  # Преобразуем в словарь

# Фильтрация для других категорий
def filter_by_sog(df):
    return df[df['Action'].str.contains("СОГЛ|СРЕДНЕЗА", case=False, na=False)]

def filter_by_auto(df):
    return df[df['Action'].str.contains("АВТООТВЕТЧИК|АССИC|ДРУГАЯ", case=False, na=False)]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)

            # Загружаем данные из CSV
            df = pd.read_csv(filename)

            # Ваши ветки
            df_first_branch = filter_by_branch(df, "ПЕРВАЯ ВЕТКА")
            df_second_branch = filter_by_branch(df, "ВТОРАЯ ВЕТКА")
            df_third_branch = filter_by_branch(df, "ТРЕТЬЯ ВЕТКА")
            df_drop_branch = filter_by_branch(df, "СБРОС")
            df_nocall_branch = filter_by_branch(df, "НЕДОЗВОН")
            df_press_branch = filter_by_branch(df, "ДОЖИМ")

            # Ваши дополнительные категории
            df_sog_branch = filter_by_sog(df)
            df_auto_branch = filter_by_auto(df)

            # Получаем результаты по каждой ветке и категории
            first_branch_summary = summarize_by_branch(df_first_branch)
            second_branch_summary = summarize_by_branch(df_second_branch)
            third_branch_summary = summarize_by_branch(df_third_branch)
            drop_branch_summary = summarize_by_branch(df_drop_branch)
            nocall_branch_summary = summarize_by_branch(df_nocall_branch)
            press_branch_summary = summarize_by_branch(df_press_branch)
            sog_branch_summary = summarize_by_branch(df_sog_branch)
            auto_branch_summary = summarize_by_branch(df_auto_branch)
            # Отображаем результаты
            return render_template('index.html', 
                                   first_branch_summary=first_branch_summary, 
                                   second_branch_summary=second_branch_summary,
                                   third_branch_summary=third_branch_summary,
                                   drop_branch_summary=drop_branch_summary,
                                   nocall_branch_summary=nocall_branch_summary,
                                   press_branch_summary=press_branch_summary,
                                   sog_branch_summary=sog_branch_summary,
                                   auto_branch_summary=auto_branch_summary)

    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
