import missingno as msno
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
import time
from IPython.display import Markdown,display
import psycopg2

#dataFrame显示设置
def pandas_df_to_Markdown_table(df):
    fmt = ['---' for i in range(len(df.columns))]
    df_fmt = pd.DataFrame([fmt],columns=df.columns)
    df_fmated = pd.concat([df_fmt,df])
    display(Markdown(df_fmated.to_csv(sep='|',index=False)))

#读取数据

#连接数据库
def connect_sql():
    try:
        conn = psycopg2.connect(database='alldata',user = 'test',password= 'test',\
                                host = '172.25.9.76',port = '9999')
        return conn
    except:
        print("can't connect database")

def read_data(tablename):
    conn = connect_sql()
    sql='select * from %s limit 100000'%tablename
    try:
        data = pd.read_sql(sql,conn)
    except Exception as e:
        print("error is %s"%e)
    conn.close()
    return data

#数据概览
data = pd.read_csv(r"E:\pycharm\pycharm_script\kaggle\fresh_comp_offline\fresh_comp_offline\tianchi_fresh_comp_train_user.csv")
pandas_df_to_Markdown_table(data.head())
type_data = data.dtypes
index_data = pd.DataFrame(type_data.index.tolist(),index=type_data.index,columns=['column'])
pandas_df_to_Markdown_table(index_data.join(type_data.to_frame(name='type')))

#字段统计信息

#数据概览，包括数值型和object类型
df_index = pd.Series(['count','unique_num','top','freq','first','last','mean','std','min','25%','50%','75%','max'])
data_desc = data.describe(include='all')
data_desc.insert(0,'statistic',data_desc.index)
data_desc = data_desc.fillna('null')
pandas_df_to_Markdown_table(data_desc)

#缺失值占比统计分析
#字段缺失分布图
mpl.rcParams['font.serif'] = ['SimHei']
mpl.rcParams['axes.unicode_minus'] = False
mpl.rcParams['font.family'] = 'sans-serif'
sns.set(font='SimHei')
#字段缺失值分布
#数据分割，防止因列数过多而导致数据显示不清晰
#字段缺失占比直方图
x=len(data)
if len(data.columns.tolist())<=50:
    plt.hist(x,data=data,bins=20)
elif 50<len(data.columns.tolist())<=100:
    plt.hist(x,data=data.iloc[:,0:50],bins=20)
    plt.hist(x,data=data.iloc[:,50:],bins=20)
else:
    plt.hist(x,data=data.iloc[:,0:50],bins=20)
    plt.hist(x,data=data.iloc[:, 50:100],bins=20)
    plt.hist(x,data=data.iloc[:, 100:],bins=20)

#数据维度
m,n = data.shape
count_list = []
column_list = []
for column in data.columns:
    count = data[column].count()
    #非空占比
    percent = round(count/m,2)
    if 0<percent<=1:
        count_list.append([column,percent,count])
        column_list.append(column)   #含有非空数值的列
#保存非空占比大于0的数据，进行下一步分析
count_none = pd.DataFrame(count_list,columns=['column','not_null_percent','not_null_count'])
count_none = count_none.sort_values(by=['not_null_percent'],ascending=False)
pandas_df_to_Markdown_table(count_none)

#去除空值列
#column参数，如果原数据没有列名，则以该参数值作为列名,若原先有列名，则从中选取该参数值所包含的列
result = pd.DataFrame(data,columns=column_list)

#异常值检验
#在1.5倍四分位差之外的数据可以被认为成异常值
#选取数值型变量，（数值型或者分类型）
numeric_list = result.select_dtypes(include=['number']).columns.tolist()
if len(numeric_list) == 0:
    print("there is no numeric column in this table")
else:
    outlier_list = []
    for column in numeric_list:
        Q3 = result[column].quantile(q=0.75)
        Q1 = result[column].quantile(q=0.25)
        outlier = result[column][(result[column]<Q1-(Q3-Q1)*1.5)|(result[column]>(Q3-Q1)*1.5+Q3)].value_counts().index.tolist()
        if len(outlier):
            outlier_list.append([outlier[0],outlier[-1],column,len(outlier)])
    if len(outlier_list):
        pandas_df_to_Markdown_table(pd.DataFrame(outlier_list,columns=['min_outlier','max_outlier','column','outlier_num']))
    else:
        print("there is no outlier in this table")


#单变量分析
#数值型单变量分析
result2 = result.fillna(0)
if len(numeric_list) == 0:
    print("there is no numeric column in this table")
else:
    for item in numeric_list:
        fig,axes = plt.subplots(1,2,figsize=(12,6))
        axes[0].set_ylabel('count')
        sns.distplot(result2[item],kde=False,ax=axes[0])
        sns.boxplot(x=item,data=result2,ax=axes[1])
        plt.show()

#分类型变量分布及图形分析
#object类型字段统计
object_data = result.select_dtypes(include=['object'])
unique_list = []
for column in object_data.columns.tolist():
    length_object = len(result[column].unique())
    #对于有太多分类的分类变量的统计意义不大
    if length_object >20:
        unique_list.append(column)
    else:
        plt.subplots(figsize=(12,12))
        sns.countplot(x=column,data=object_data)
        plt.show()
