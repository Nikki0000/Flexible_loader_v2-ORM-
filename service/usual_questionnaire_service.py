import pandas as pd
from sqlalchemy.orm import sessionmaker
from model import Questionnaire, QuestionnaireHeader, Question, QuestionConfiguration, QuestionAnswer, QuestionnaireToTaskType, QuestionnaireToTaskTypeSpecialization
from logger import Logger
from datetime import datetime
import re

from service.base_servise import BaseService

class UsualQuestionnaireService(BaseService):
    def __init__(self, file_path, engine):
        self.file_path = file_path
        self.engine = engine
        self.logger = Logger()

    # верификация данных
    def verify(self, questionnaire_df, header_and_question_df):
        try:
            if questionnaire_df.empty:
                raise ValueError("not enough data in list Questionnaire")
            
            if len(questionnaire_df.columns) < 2:
                raise ValueError("not enough columns in list Questionnaire")
            
            if header_and_question_df.empty:
                raise ValueError("not enough data in list HeaderAndQuestion")

        except Exception as e:
            print(f"Error verification data: {e}")
            raise

    # читаем данных
    def load_data(self):
        try:
            #Читаем лист Questionnaire
            questionnaire_df = pd.read_excel(self.file_path, sheet_name='Questionnaire')

            #Читаем лист QuestionAndHeader
            header_and_question_df = pd.read_excel(self.file_path, sheet_name='HeaderAndQuestion')

            self.verify(questionnaire_df, header_and_question_df)

            questionnaire_name = questionnaire_df.iloc[0, 0]
            # visit_type = [vt.strip() for vt in questionnaire_df.iloc[0, 1].split(',')]
            visit_types = questionnaire_df.iloc[0, 1]
            specializations = questionnaire_df.iloc[0, 2] if len(questionnaire_df.columns) > 2 else None

            return questionnaire_name, visit_types, specializations, header_and_question_df
    
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")
            raise


    # загружаем данные
    def insert_data(self, questionnaire_name, visit_types, specializations, header_and_question_df):
        Session = sessionmaker(bind=self.engine)
        session = Session()

        try:
            # добавляем анкету
            questionnaire = Questionnaire(Name=questionnaire_name, CreatedOn=datetime.utcnow(), ModifiedOn=datetime.utcnow())
            session.add(questionnaire)
            session.commit()  # фиксируем изменения для получения id

            self.logger.log_to_file(f"Added Questionnaire: {questionnaire.Name}")

            # task_type = QuestionnaireToTaskType(QuestionnaireId=int(questionnaire.Id), TaskTypeId=int(visit_type), CreatedOn=datetime.utcnow(), ModifiedOn=datetime.utcnow(), Order=0)
            # session.add(task_type)
            # session.commit()
            # print(visit_types)
            visit_types = str(visit_types)
            visit_types = re.sub(r'\s+', '', visit_types)
            visit_types = visit_types.split(',')
            visit_types = list(map(int, visit_types))

            # if isinstance(visit_types, str):
            #     visit_types = visit_types.split(',')
            # elif isinstance(visit_types, (int, float)):
            #     visit_types = [visit_types]
            # elif isinstance(visit_types, list):
            #     visit_types = [str(vt).strip() for vt in visit_types]
            # else:
            #     raise ValueError(f"Unsupported type for visit_types: {type(visit_types)}")

            # print(visit_types)

            task_type_ids = []
            
            for order in range(len(visit_types)):
                task_type = QuestionnaireToTaskType(QuestionnaireId=int(questionnaire.Id), TaskTypeId=int(visit_types[order]), CreatedOn=datetime.utcnow(), ModifiedOn=datetime.utcnow(), Order=order)
                session.add(task_type)
                session.commit()
                task_type_ids.append(task_type.Id)
                self.logger.log_to_file(f"Added QuestionnaireToTaskType: QuestionnaireId={questionnaire.Id}, TaskTypeId={visit_types[order]}, Order={order}")
            
            if specializations:
                specializations = str(specializations)
                specializations = re.sub(r'\s+', '', specializations)
                specializations = specializations.split(',')
                specializations = list(map(int, specializations))

                for task_type_id in task_type_ids:
                    for specialization in specializations:
                        specialization_entry = QuestionnaireToTaskTypeSpecialization(
                            QuestionnaireId=int(questionnaire.Id),
                            SpecializationId=int(specialization),
                            QuestionnaireToTaskTypeId=int(task_type_id),
                            CreatedOn=datetime.utcnow(),
                            ModifiedOn=datetime.utcnow()
                        )
                        session.add(specialization_entry)
                        session.commit()
                        self.logger.log_to_file(f"Added QuestionnaireToTaskTypeSpecialization: QuestionnaireId={questionnaire.Id}, SpecializationId={specialization}, TaskTypeId={task_type_id}")


            # добавляем хэдер и вопросы
            # headers = {}
            # row_number = 1
            for row_idx in range(header_and_question_df.shape[0]):
                header_name = header_and_question_df.iloc[row_idx, 0]
                question_name = header_and_question_df.iloc[row_idx, 1]
                answer_type = header_and_question_df.iloc[row_idx, 2]
                answer_options = header_and_question_df.iloc[row_idx, 3] if answer_type == 4 else None

                header = session.query(QuestionnaireHeader).filter_by(Name=header_name).first()
                if not header:
                    header = QuestionnaireHeader(Name=header_name, Visible=True, Position=row_idx+1, CreatedOn=datetime.utcnow(), ModifiedOn=datetime.utcnow())
                    session.add(header)
                    session.commit()
                    self.logger.log_to_file(f"Added QuestionnaireHeader: {header.Name}")

                question = Question(Type=int(answer_type), QuestionnaireId=int(questionnaire.Id), Order=row_idx+1, Name=question_name, CreatedOn=datetime.utcnow(), ModifiedOn=datetime.utcnow())
                session.add(question)
                session.commit()  # фиксируем изменения для получения id

                self.logger.log_to_file(f"Added Question: {question.Name}")

                configuration = QuestionConfiguration(QuestionId=int(question.Id), QuestionnaireHeaderId=int(header.Id), RowNumber=row_idx+1, CreatedOn=datetime.utcnow(), ModifiedOn=datetime.utcnow())
                session.add(configuration)
                session.commit()  # фиксируем изменения для получения id

                self.logger.log_to_file(f"Added QuestionConfiguration: QuestionId={configuration.QuestionId}, HeaderId={configuration.QuestionnaireHeaderId}")
                
                if int(answer_type) == 4 and answer_options:
                    options = answer_options.split(',')
                    order = 1
                    for idx, option in enumerate(options, start=1):
                        question_answer = QuestionAnswer(QuestionId=question.Id, Order=idx, Name=option.strip(), CreatedOn=datetime.utcnow(), ModifiedOn=datetime.utcnow())
                        session.add(question_answer)
                    session.commit()
                    self.logger.log_to_file(f"Added QuestionAnswer for QuestionId={question.Id}")

            session.commit()

        except Exception as e:
            session.rollback()
            print(f"Error: {e}")
        finally:
            session.close()

