from sqlalchemy import create_engine,Column,String,LargeBinary,Float,Integer,ForeignKey
from sqlalchemy.orm import sessionmaker,relationship
from sqlalchemy.ext.declarative import declarative_base
import pymysql

Base = declarative_base()
class User(Base):
    __tablename__='user'
    id = Column(Integer(),nullable=True,primary_key=True)
    name = Column(String(20),nullable=True)
    password = Column(String(20),nullable=True,default='保密')
    record = relationship(argument='Record',   # 关联的类的名字
                           backref='user',
                           cascade='all,delete'   #设置删除用户记录之后，关联表自动删除
                           )  # 使用参数 uselist=False，就是一对一的表了
class Record(Base):
    __tablename__='record'
    id = Column(Integer(),nullable=True,primary_key=True)
    img = Column(LargeBinary(),nullable=False)
    label = Column(Integer(),nullable=False)
    score = Column(Float(),nullable=False)
    user_id = Column(Integer(),ForeignKey('user.id')) # 外键
engine = create_engine("mysql+pymysql://root:root@localhost:3306/planteye",echo=False)
# Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
session = sessionmaker(bind=engine)
sess = session()
sess.add(User(name='js',password='js'))
sess.commit()