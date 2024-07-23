from model import Base, get_engine
from service.usual_questionnaire_service import UsualQuestionnaireService
from config import db_connection

def main():
    file_path = 'files/filev2.xlsx'

    engine = get_engine(db_connection)
    Base.metadata.create_all(engine)

    # data_loader = DataLoader(file_path)
    # questionnaire_name, visit_types, specializations, header_and_question_df = data_loader.load_data()

    # data_processor = DataProcessor(engine)
    # data_processor.insert_data(questionnaire_name, visit_types, specializations, header_and_question_df)

    service = UsualQuestionnaireService(file_path, engine)
    questionnaire_name, visit_types, specializations, header_and_question_df = service.load_data()
    service.insert_data(questionnaire_name, visit_types, specializations, header_and_question_df)

if __name__ == '__main__':
    main()
    