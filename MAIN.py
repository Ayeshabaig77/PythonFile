from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, Boolean, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import JSON  # Import JSON type from sqlalchemy.types
import subprocess
import os

Base = declarative_base()

from sqlalchemy.types import JSON

class FeeDefaulter(Base):
    __tablename__ = 'fee_defaulters'

    university_id = Column(Integer, ForeignKey('students.university_id'), primary_key=True)
    student = relationship('Student', back_populates='fee_defaulter')


class Student(Base):
    __tablename__ = 'students'

    university_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    fee_passed = Column(Boolean, nullable=False, default=False)
    cgpa = Column(Float, nullable=False)
    date_of_birth = Column(String, nullable=False)
    department = Column(String, nullable=False)
    semester = Column(Integer, nullable=False)
    courses = relationship('StudentCourse', back_populates='student', cascade="all, delete-orphan")
    passed_prerequisites = Column(JSON)
    fee_defaulter = relationship('FeeDefaulter', back_populates='student', cascade="all, delete")
  # Relationship with FeeDefaulter table
    fee_challans = relationship('FeeChallan', back_populates='student')  # Relationship with FeeChallan table


class StudentCourse(Base):
    __tablename__ = 'student_courses'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.university_id'))
    course_id = Column(String, ForeignKey('courses.course_id'))
    student = relationship('Student', back_populates='courses')
    course = relationship('Course')


class Course(Base):
    __tablename__ = 'courses'

    course_id = Column(String, primary_key=True)
    course_name = Column(String, nullable=False)
    fee = Column(Float, nullable=False)
    credit_hours = Column(Integer, nullable=False)  # Add credit hours column
    prerequisites = relationship('Prerequisite', back_populates='course', cascade="all, delete-orphan")



class Prerequisite(Base):
    __tablename__ = 'prerequisites'

    prerequisite_course_id = Column(String, primary_key=True)
    course_id = Column(String, ForeignKey('courses.course_id'))
    prerequisite_course_name = Column(String, nullable=False)
    course = relationship('Course', back_populates='prerequisites')


class FeeChallan(Base):
    __tablename__ = 'fee_challans'

    challan_id = Column(Integer, primary_key=True)
    university_id = Column(Integer, ForeignKey('students.university_id'), nullable=False)
    course_id = Column(String, ForeignKey('courses.course_id'), nullable=False)
    fee_amount = Column(Float, nullable=False)
    student = relationship('Student', back_populates='fee_challans')


class Admin(Base):
    __tablename__ = 'admins'

    admin_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)

    def delete_student(self, session, university_id):
        try:
            student = session.query(Student).filter_by(university_id=university_id).first()
            if student:
                session.delete(student)
                session.commit()
                print(f"Student with university ID {university_id} deleted successfully.")
            else:
                print("Student not found.")
        except Exception as e:
            print("Error deleting student:", e)

    def delete_batch_advisor(self, session, advisor_id):
        try:
            advisor = session.query(BatchAdvisor).filter_by(advisor_id=advisor_id).first()
            if advisor:
                session.delete(advisor)
                session.commit()
                print(f"Batch advisor with ID {advisor_id} deleted successfully.")
            else:
                print("Batch advisor not found.")
        except Exception as e:
            print("Error deleting batch advisor:", e)

    def view_all_courses(self, session):
        try:
            courses = session.query(Course).all()
            print("Available Courses:")
            for course in courses:
                prereqs = ", ".join([prerequisite.prerequisite_course_name for prerequisite in course.prerequisites])
                print(f"Course ID: {course.course_id}, Course Name: {course.course_name}, Credit Hours: {course.credit_hours}, Fee: {course.fee}, Prerequisites: {prereqs}")
        except Exception as e:
            print("Error viewing all courses:", e)


    def view_all_students(self, session):
     try:
        students = session.query(Student).all()
        print("Registered Students:")
        for student in students:
            print("-" * 60)  # Upper dashed line
            print(f"University ID: {student.university_id}".ljust(30) + f"Name: {student.name}")
            print(f"Email: {student.email}".ljust(30) + f"Department: {student.department}")
            print(f"Semester: {student.semester}".ljust(30) + f"Courses: {', '.join([student_course.course.course_name for student_course in student.courses])}")
            print(f"Fee Status: {'Paid' if student.fee_passed else 'Pending'}".ljust(30) + f"CGPA: {student.cgpa}")
            print(f"Date of Birth: {student.date_of_birth}".ljust(30))

            # Fetch and display fee challans for the current student
            fee_challans = session.query(FeeChallan).filter_by(university_id=student.university_id).all()
            if fee_challans:
                print("Fee Challans:")
                for challan in fee_challans:
                    print(f"Challan ID: {challan.challan_id}")
                    print(f"Course ID: {challan.course_id}")
                    print(f"Fee Amount: {challan.fee_amount}")
            else:
                print("No fee challans found.")

     except Exception as e:
        print("Error viewing all students:", e)



    def view_all_fee_challans(self, session):
        try:
            fee_challans = session.query(FeeChallan).all()
            print("Fee Challans of Students:")
            for challan in fee_challans:
                print(f"Challan ID: {challan.challan_id}".ljust(20) + f"University ID: {challan.university_id}".ljust(20) + f"Course ID: {challan.course_id}".ljust(20) + f"Fee Amount: {challan.fee_amount}")
        except Exception as e:
            print("Error viewing all fee challans:", e)

    def create_course_with_prerequisites(self, session):
     course_id = input("Enter the course ID: ")
     course_name = input("Enter the name of the new course: ")
     course_fee = float(input("Enter the fee for the course: "))
     credit_hours = int(input("Enter the credit hours for the course: "))  # Add credit hours input
     prerequisites_str = input("Enter comma-separated prerequisite course IDs and names (if any), or leave blank: ")
     prerequisites_list = [item.strip().split(':') for item in prerequisites_str.split(',')]

     try:
        course = Course(
            course_id=course_id,
            course_name=course_name,
            fee=course_fee,
            credit_hours=credit_hours  # Assign credit hours to the course
        )

        for prereq_id, prereq_name in prerequisites_list:
            prerequisite = Prerequisite(
                prerequisite_course_id=prereq_id,
                prerequisite_course_name=prereq_name,
                course=course
            )
            session.add(prerequisite)

        session.add(course)
        session.commit()
        print("Course created successfully.")
     except Exception as e:
        print("Error creating course with prerequisites:", e)


    def set_fee_structure(self, session):
        try:
            course_id = input("Enter the course ID for which you want to set the fee: ")
            course_fee = float(input("Enter the new fee for the course: "))
            course = session.query(Course).filter_by(course_id=course_id).first()
            if course:
                course.fee = course_fee
                session.commit()
                print("Fee structure updated successfully.")
            else:
                print("Course not found.")
        except Exception as e:
            print("Error setting fee structure:", e)


class BatchAdvisor(Base):
    __tablename__ = 'batch_advisors'

    advisor_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    qualification = Column(String, nullable=False)
    department = Column(String, nullable=False)

    def display_menu(self):
        print("\nBatch Advisor Menu:")
        print("1. View Registered Students by Department")
        print("2. View All Courses")
        #print("3. Create Account")
        print("3. Exit")

    def process_choice(self, choice, session):
        if choice == '1':
            self.view_students_by_department(session)
        elif choice == '2':
            self.view_all_courses(session)
        elif choice == '3':
            print("Exiting...")
        else:
            print("Invalid choice.")
    
    @classmethod
    def login(cls, session):
        advisor_id = input("Enter your advisor ID to Login: ")
        existing_advisor = session.query(BatchAdvisor).filter_by(advisor_id=advisor_id).first()
        if existing_advisor:
            print(f"Welcome back, {existing_advisor.name}!")
            return existing_advisor
        else:
            create_account_choice = input("Advisor not found. Do you want to create an account? (yes/no): ").lower()
            if create_account_choice == 'yes':
                return cls.create_account(session, advisor_id)  # Pass the advisor_id to create_account method
            else:
                print("Returning to main menu.")
                return None

    @staticmethod
    def create_account(session, advisor_id):  # Accept advisor_id as an argument
        name = input("Enter your name: ")
        email = input("Enter your email: ")
        qualification = input("Enter your qualification: ")
        department = input("Enter your department: ")
        new_advisor = BatchAdvisor(advisor_id=advisor_id, name=name, email=email, qualification=qualification, department=department)  # Include advisor_id when creating a new advisor
        session.add(new_advisor)
        session.commit()
        print("Account created successfully.")
        return new_advisor
    
    def view_fee_defaulters(self, session):
        try:
            fee_defaulters = session.query(FeeDefaulter).all()
            if fee_defaulters:
                print("Fee Defaulters:")
                for defaulter in fee_defaulters:
                    student = session.query(Student).filter_by(university_id=defaulter.university_id).first()
                    if student:
                        print(f"University ID: {student.university_id}, Name: {student.name}, Email: {student.email}")
            else:
                print("No fee defaulters found.")
        except Exception as e:
            print("Error viewing fee defaulters:", e)
    
    def view_students_by_department(self, session):
        try:
            department = input("Enter the department to view registered students: ")
            students = session.query(Student).filter_by(department=department).all()
            if students:
                print(f"\nRegistered Students in Department {department}:")
                for student in students:
                    print("-" * 60)  # Upper dashed line
                    print(f"University ID: {student.university_id}".ljust(30) + f"Name: {student.name}")
                    print(f"Email: {student.email}".ljust(30) + f"Department: {student.department}")
                    print(f"Semester: {student.semester}".ljust(30) + f"Courses: {', '.join([course.course_id for course in student.courses])}")
                    print(f"Fee Status: {'Paid' if student.fee_passed else 'Pending'}".ljust(30) + f"CGPA: {student.cgpa}")
                    print(f"Date of Birth: {student.date_of_birth}".ljust(30), end="")

                    # Fetch and display fee challans for the current student
                    fee_challans = session.query(FeeChallan).filter_by(university_id=student.university_id).all()
                    if fee_challans:
                        print(f"Fee Challans: {', '.join([str(challan.challan_id) for challan in fee_challans])}")
                    else:
                        print("No fee challans found.")
            else:
                print("No students found in the department.")
        except Exception as e:
            print("Error viewing students by department:", e)

    def view_all_courses(self, session):
        try:
            courses = session.query(Course).all()
            print("Available Courses:")
            for course in courses:
                print(f"Course ID: {course.course_id}".ljust(20) + f"Course Name: {course.course_name}".ljust(40) + f"Fee: {course.fee}")
        except Exception as e:
            print("Error viewing all courses:", e)


class Database:
    def __init__(self, dbname):
        self.engine = create_engine(f'sqlite:///{dbname}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def generate_erd(self):
        try:
            # Save the SQLAlchemy models to a temporary Python file
            with open("models.py", "w") as f:
                f.write("# SQLAlchemy models\n\n")
                f.write(inspect.getsource(Student))
                f.write(inspect.getsource(StudentCourse))
                f.write(inspect.getsource(Course))
                f.write(inspect.getsource(Prerequisite))
                f.write(inspect.getsource(FeeChallan))
                f.write(inspect.getsource(Admin))
                f.write(inspect.getsource(BatchAdvisor))

            # Use the SQLAlchemy Schema Visualizer extension to generate the ERD
            subprocess.run(["code", "--install-extension", "msyerli.vscode-sqlalchemy-schema"])
            subprocess.run(["code", "--new-window", "models.py"])
            subprocess.run(["code", "--new-window", "--wait", "--command", "extension.sqlAlchemySchemaVisualizer.generateDiagram"])
            
            # Remove the temporary Python file
            os.remove("models.py")

            print("ERD generated successfully.")
        except Exception as e:
            print("Error generating ERD:", e)

    def admin_operations(self):
        admin = self.session.query(Admin).first()
        if not admin:
            print("No admin found in the database.")
            return
        while True:
            print("\nAdmin Menu:")
            print("1. Create Course with Prerequisites")
            print("2. Set Fee Structure")
            print("3. View all Courses")
            print("4. View all Students")
            print("5. View all Fee Challans")
            print("6. View Fee Defaulters")
            print("7. Delete Student")
            print("8. Delete Batch Advisor")
            print("9. Back")

            admin_choice = input("Select an option: ")

            if admin_choice == '1':
                admin.create_course_with_prerequisites(self.session)
            elif admin_choice == '2':
                admin.set_fee_structure(self.session)
            elif admin_choice == '3':
                admin.view_all_courses(self.session)
            elif admin_choice == '4':
                admin.view_all_students(self.session)
            elif admin_choice == '5':
                admin.view_all_fee_challans(self.session)
            elif admin_choice == '6':
                admin.view_fee_defaulters(self.session)
            elif admin_choice == '7':
                university_id = input("Enter the university ID of the student to delete: ")
                admin.delete_student(self.session, university_id)
            elif admin_choice == '8':
                advisor_id = input("Enter the advisor ID of the batch advisor to delete: ")
                admin.delete_batch_advisor(self.session, advisor_id)
            elif admin_choice == '9':
                print("Returning to main menu.")
                break  # Break out of the loop and return to the main menu
            else:
                print("Invalid choice. Please select again.")

    def insert_student(self, university_id, name, email, dob, cgpa, department, semester, fee_passed):
        try:
            student = Student(
                university_id=university_id,
                name=name,
                email=email,
                date_of_birth=dob,
                cgpa=cgpa,
                department=department,   # Assign department to student
                semester=semester,       # Assign semester to student
                fee_passed=fee_passed,
            )
            self.session.add(student)
            self.session.commit()
            print("Student registered successfully.")
        except Exception as e:
            print("Error inserting student:", e)

    def register_for_course(self, student_id):
        try:
            # Fetch the student from the database
            student = self.session.query(Student).filter_by(university_id=student_id).first()
            if not student:
                print("Student not found.")
                return

            # Display available courses for registration
            print("Available Courses for Registration:")
            courses = self.session.query(Course).all()
            for course in courses:
                print(f"Course ID: {course.course_id}, Course Name: {course.course_name}, Fee: {course.fee}, Prerequisites: {', '.join([prereq.prerequisite_course_name for prereq in course.prerequisites])}")

            # Prompt the student to select a course for registration
            course_id = input("Enter the course ID you want to register for: ")
            course = self.session.query(Course).filter_by(course_id=course_id).first()
            if not course:
                print("Course not found.")
                return

            # Check if the student has passed the prerequisites for the selected course
            passed_prereqs = True
            if course.prerequisites:
                passed_prereqs_input = input("Enter the names of the prerequisite courses you have passed (comma-separated): ")
                passed_prereqs_list = passed_prereqs_input.split(',')
                passed_prereqs_set = set(passed_prereqs_list)
                course_prereqs_set = set([prereq.prerequisite_course_name for prereq in course.prerequisites])

                if not passed_prereqs_set.issuperset(course_prereqs_set):
                    passed_prereqs = False

            if passed_prereqs:
                # Update the passed prerequisites for the student
                student.passed_prerequisites = list(passed_prereqs_set)

                # Check if the student is already registered for the course
                if course in student.courses:
                    print("You are already registered for this course.")
                    return

                # Register the student for the selected course
                student_course = StudentCourse(student_id=student.university_id, course_id=course.course_id)
                self.session.add(student_course)
                self.session.commit()
                print(f"Successfully registered for course {course.course_name}.")

                # Check if the fee is cleared for all registered courses
                self.update_student_fee_status(student)

            else:
                print("You can't register for this course as you have not passed the prerequisites.")

        except Exception as e:
            print("Error registering for course:", e)
    
    def update_student_fee_status(self, student):
        try:
            fee_defaulters = []
            for course in student.courses:
                # Fetch fee challans for each registered course
                fee_challan = self.session.query(FeeChallan).filter_by(university_id=student.university_id, course_id=course.course_id).first()
                if not fee_challan:
                    fee_defaulters.append(course.course_name)

            # Update fee_passed status based on fee clearance
            student.fee_passed = not bool(fee_defaulters)

            # If the student is a fee defaulter, store their information in the FeeDefaulter table
            if fee_defaulters:
                fee_defaulter = FeeDefaulter(university_id=student.university_id)
                self.session.add(fee_defaulter)
                self.session.commit()

        except Exception as e:
            print("Error updating student fee status:", e)
            
    def view_fee_defaulters(self, session):
        try:
            fee_defaulters = session.query(FeeDefaulter).all()
            if fee_defaulters:
                print("Fee Defaulters:")
                for defaulter in fee_defaulters:
                    student = session.query(Student).filter_by(university_id=defaulter.university_id).first()
                    if student:
                        print(f"University ID: {student.university_id}, Name: {student.name}, Email: {student.email}")
            else:
                print("No fee defaulters found.")
        except Exception as e:
            print("Error viewing fee defaulters:", e)
    
    def display_registered_courses(self, student_id):
        try:
        # Fetch the student from the database
         student = self.session.query(Student).filter_by(university_id=student_id).first()
         if not student:
            print("Student not found.")
            return

         # Display the courses registered by the student
         if student.courses:
            print("Registered Courses:")
            for student_course in student.courses:
                course_id = student_course.course_id
                # Fetch the course details from the 'courses' table using the course_id
                course = self.session.query(Course).filter_by(course_id=course_id).first()
                if course:
                    print(f"Course ID: {course.course_id}, Course Name: {course.course_name}, Fee: {course.fee}")
                else:
                    print(f"Course ID: {course_id} (Course details not found)")
         else:
            print("No courses registered yet.")
        except Exception as e:
         print("Error displaying registered courses:", e)


    def display_courses_with_fee(self, student_id):
     try:
        student = self.session.query(Student).filter_by(university_id=student_id).first()
        if not student:
            print("Student not found.")
            return

        if student.courses:
            print("Courses with Fee Details:")
            for student_course in student.courses:
                course_id = student_course.course_id
                course = self.session.query(Course).filter_by(course_id=course_id).first()
                if course:
                    print(f"Course ID: {course.course_id}, Course Name: {course.course_name}, Fee: {course.fee}")
                else:
                    print(f"Course ID: {course_id} (Course details not found)")
        else:
            print("No courses registered yet.")
     except Exception as e:
        print("Error displaying courses with fee:", e)


    def pay_fee_for_course(self, student_id):
        try:
            self.display_courses_with_fee(student_id)
            course_id = input("Enter the ID of the course for which you want to pay the fee: ")
            fee_amount = float(input("Enter the fee amount: "))

            student = self.session.query(Student).filter_by(university_id=student_id).first()
            course = self.session.query(Course).filter_by(course_id=course_id).first()

            if not student or not course:
                print("Invalid student or course ID.")
                return

            fee_challan = FeeChallan(university_id=student_id, course_id=course_id, fee_amount=fee_amount)
            self.session.add(fee_challan)
            self.session.commit()
            print("Fee payment successful.")
        except ValueError:
            print("Invalid fee amount. Please enter a valid number.")
        except Exception as e:
            print("Error paying fee for course:", e)

def main():
    dbname = "COURSE_REGISTRATION_SYSTEM.db"
    db = Database(dbname)

    while True:
        print("\nUniversity Course Registration System")
        print("1. Admin")
        print("2. Student")
        print("3. Batch Advisor")
        print("4. Exit")

        role_choice = input("Select your role: ")

        if role_choice == '1':
            db.admin_operations()

        elif role_choice == '2':
            student_id = input("Enter your university ID to Login: ")
            existing_student = db.session.query(Student).filter_by(university_id=student_id).first()
            if existing_student:
                print(f"Welcome back, {existing_student.name}!")
                while True:
                    print("\nStudent Operations:")
                    print("1. Register for Course")
                    print("2. Display Registered Courses")
                    print("3. Pay Fee")
                    print("4. Back")

                    student_choice = input("Select an option: ")

                    if student_choice == '1':
                        db.register_for_course(student_id)
                    elif student_choice == '2':
                        db.display_registered_courses(student_id)
                    elif student_choice == '3':
                        db.pay_fee_for_course(student_id)
                    elif student_choice == '4':
                        break
                    else:
                        print("Invalid choice.")
            else:
                register_choice = input("Student not found. Do you want to register? (yes/no): ").lower()
                if register_choice == 'yes':
                    name = input("Enter your name: ")
                    email = input("Enter your email: ")
                    dob = input("Enter your date of birth (YYYY-MM-DD): ")
                    cgpa = float(input("Enter your CGPA: "))
                    department = input("Enter your department: ")  # Prompt for department
                    semester = int(input("Enter your semester: "))  # Prompt for semester
                    fee_cleared = input("Has the fee been cleared (yes/no)? ").lower()

                    fee_passed = True if fee_cleared == 'yes' else False
                    db.insert_student(student_id, name, email, dob, cgpa, department, semester, fee_passed)
                else:
                    print("Returning to main menu.")

        elif role_choice == '3':
            advisor = BatchAdvisor.login(db.session)
            if advisor:
                while True:
                    advisor.display_menu()
                    advisor_choice = input("Enter your choice: ")
                    if advisor_choice == '1':
                        advisor.view_students_by_department(db.session)
                    elif advisor_choice == '2':
                        advisor.view_all_courses(db.session)
                    elif advisor_choice == '3':
                        print("Exiting...")
                        break
                    else:
                        print("Invalid choice.")

        elif role_choice == '4':
            print("Exiting...")
            break

        else:
            print("Invalid choice. Please select again.")


if __name__ == "__main__":
    main()