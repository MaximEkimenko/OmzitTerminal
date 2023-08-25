## project tables

### st_table (shift_task_table)

```
with sqlite3.connect("terminal.db") as con:
    cur = con.cursor()
    cur.execute(""" CREATE TABLE IF NOT EXISTS st_table(
        id INTEGER PRIMARY KEY AUTOINCREMENT, # id СЗ +
        op_name TEXT,  # наименование операции СЗ + 
        model TEXT,  # модель изделия СЗ      + 
        norm_tech REAL, # технологическая норма времени СЗ +   
        order TEXT,  # номер изделия (заказа)   + 
        workshop INTEGER,  # номер цеха + 
        datetime_plan_ws TEXT, # время планирования на цех 
        dispatcher_plan_ws TEXT,  # ФИО диспетчера запланировал
        datetime_plan_wp TEXT,  # время планирования ра РЦ
        dispatcher_plan_wp TEXT, # ФИО диспетчера планирования на РЦ
        master_assign_wp TEXT,  # ФИО мастера распределения 
        datetime_assign_wp TEXT,  # время распределения 
        datetime_job_start TEXT, # время начала работ
        datetime_master_call TEXT, # время вызова мастера
        master_calls INTEGER, # количество вызовов мастера
        norm_fact REAL,  # фактическая норма времени СЗ
        master_finish_wp TEXT,  # ФИО мастера вызвавшего ОТК  
        datetime_otk_call TEXT,  # время вызова контролёра ОТК
        otk_answer TEXT,  # ФИО ответившего контролёра
        datetime_otk_answer TEXT,  # время ответа контролёра 
        otk_decision TEXT,  # ФИО контролёра выполневшего приёмку
        decision_time TEX,  # длительность приёмки
        st_status TEXT NOT NULL DEFAULT не запланировано  # статус СЗ 
    );""")
```

### model_list
```
with sqlite3.connect("terminal.db") as con:
    cur = con.cursor()
    cur.execute(""" CREATE TABLE IF NOT EXISTS models(
        id INTEGER PRIMARY KEY AUTOINCREMENT, # id модели
        model_name TEXT # имя модели
    );""")
```


### tech_data

```
with sqlite3.connect("terminal.db") as con:
    cur = con.cursor()
    cur.execute(""" CREATE TABLE IF NOT EXISTS tech_table(
        id INTEGER PRIMARY KEY AUTOINCREMENT, # id записи
        FOREIGN KEY(model_id) REFERENCES models(id),   #  ссылка на model_id в таблице models
        model_name TEXT,  # модель изделия СЗ
        op_name TEXT,  # наименование операции 
        ws_name TEXT, # имя рабочего центра
        ws_number TEXT, # номе рабочего центра
        norm_tech REAL, # технологическая норма времени СЗ
        datetime_update TEXT, # время последнего обновления данных
          
    );""")
```


