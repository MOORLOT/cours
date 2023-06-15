import asyncpg
import disnake
import random
import datetime

from disnake.ext import commands
from datetime import datetime, timedelta
from main import bot


def is_admin():
    def predicate(ctx):
        return ctx.author.guild_permissions.administrator

    return commands.check(predicate)


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = None

    async def connect_to_database(self):
        self.conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='1',
            database='Coursework'
        )
        print(f"{bot.user.name}: I have connection with the database (class: StudentDatabase).")
        await self.create_table_if_not_exists()

    async def create_table_if_not_exists(self):
        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id SERIAL PRIMARY KEY,
                name VARCHAR
            )
        ''')

        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id SERIAL PRIMARY KEY,
                first_name VARCHAR,
                last_name VARCHAR,
                email VARCHAR
            )
        ''')

        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id SERIAL PRIMARY KEY,
                name VARCHAR,
                teacher_id INT,
                FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id)
            )
        ''')

        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id SERIAL PRIMARY KEY,
                first_name VARCHAR,
                last_name VARCHAR,
                email VARCHAR,
                group_id INT,
                FOREIGN KEY (group_id) REFERENCES groups(group_id)
            )
        ''')

        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS grades (
                grade_id SERIAL PRIMARY KEY,
                student_id INT,
                subject_id INT,
                value DECIMAL,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
            )
        ''')

        await self.conn.execute('''
            CREATE TABLE IF NOT EXISTS log_table (
            log_id SERIAL PRIMARY KEY,
            table_name VARCHAR,
            action VARCHAR,
            old_data JSONB,
            new_data JSONB,
            timestamp TIMESTAMP(0) DEFAULT NOW()
            )
        ''')

    async def close_database_connection(self):
        if self.conn:
            await self.conn.close()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.connect_to_database()

    @commands.Cog.listener()
    async def on_cog_unload(self):
        await self.close_database_connection()

    async def add_student_to_database(self, student_data):
        await self.conn.execute('''
            INSERT INTO students (first_name, last_name, email, group_id)
            VALUES ($1, $2, $3, $4)
        ''', student_data['name'], student_data['last_name'], student_data['email'], student_data['group_id'])

    async def add_course_to_database(self, course_data):
        await self.conn.execute('''
            INSERT INTO subjects (name, teacher_id)
            VALUES ($1, $2)
        ''', course_data['course_name'], course_data['teacher_id'])
        # Отримуємо ID створеного предмета
        subject_id = await self.conn.fetchval('SELECT subject_id FROM subjects WHERE name = $1',
                                              course_data['course_name'])

        await self.conn.execute('''
            INSERT INTO grades (student_id, subject_id)
            VALUES ($1, $2)
        ''', course_data['student_id'], subject_id)

    async def add_grade_to_database(self, grade_data):
        await self.conn.execute('''
            INSERT INTO grades (student_id, subject_id, value)
            VALUES ($1, $2, $3)
        ''', grade_data['student_id'], grade_data['subject_id'], grade_data['grade'])

    async def get_log_data(self, date):
        query = """
        SELECT *
        FROM log_table
        WHERE timestamp >= $1
        """
        values = (date,)

        try:
            result = await self.conn.fetch(query, *values)
            return result
        except Exception as e:
            # Обробка помилки
            # ...
            return None

    async def update_student_in_database(self, student_data):
        query = """
        UPDATE Students
        SET first_name  = $1, last_name = $2, email = $3, group_id = $4
        WHERE student_id = $5
        """
        values = (
            student_data['first_name'],
            student_data['last_name'],
            student_data['email'],
            student_data['group_id'],
            student_data['student_id']
        )
        await self.conn.execute(query, *values)

    async def get_top_students_data(self):
        query = """
           SELECT student_name, average_grade
           FROM get_top_students()
           """
        try:
            result = await self.conn.fetch(query)
            return result
        except Exception as e:
            # Обробка помилки
            # ...
            return None

    @commands.slash_command(description="Додати студента до бази даних")
    @is_admin()
    async def add_student(self, ctx, name: str, last_name: str, email: str, group_id: int):
        student_data = {
            'name': name,
            'last_name': last_name,
            'email': email,
            'group_id': group_id
        }

        result = await self.add_student_to_database(student_data)
        if not result:
            error_embed = disnake.Embed(title="Помилка", description=f"Додати дані не вдалось",
                                        color=0xFF0000)
            await ctx.send(embed=error_embed)
        else:
            embed = disnake.Embed(title="Успішно", description="Студент був доданий до бази даних.", color=0x00FF00)
            await ctx.send(embed=embed)

    @commands.slash_command(description="Додати курс до бази даних")
    @is_admin()
    async def add_course(self, ctx, course_name: str, teacher_id: int, student_id: int):
        course_data = {
            'course_name': course_name,
            'teacher_id': teacher_id,
            'student_id': student_id
        }

        result = await self.add_course_to_database(course_data)
        if not result:
            error_embed = disnake.Embed(title="Помилка", description=f"Додати дані не вдалось",
                                        color=0xFF0000)
            await ctx.send(embed=error_embed)
        else:
            embed = disnake.Embed(title="Успішно", description="Курс був доданий до бази даних.", color=0x00FF00)
            await ctx.send(embed=embed)

    @commands.slash_command(description="Додати оцінку до бази даних")
    @is_admin()
    async def add_grade(self, ctx, student_id: int, subject_id: int, grade: int):
        grade_data = {
            'student_id': student_id,
            'subject_id': subject_id,
            'grade': grade
        }

        result = await self.add_grade_to_database(grade_data)
        if not result:
            error_embed = disnake.Embed(title="Помилка", description=f"Додати дані не вдалось",
                                        color=0xFF0000)
            await ctx.send(embed=error_embed)
        else:
            embed = disnake.Embed(title="Успішно", description="Оцінка була додана до бази даних.", color=0x00FF00)
            await ctx.send(embed=embed)

    @commands.slash_command(description="Вивести дані з таблиці викладачів")
    async def show_teachers(self, ctx):
        teachers = await self.conn.fetch('SELECT * FROM teachers')
        for teacher in teachers:
            embed = disnake.Embed(title="Teacher", color=0xE28CC0)
            embed.add_field(name=f"ID: {teacher['teacher_id']}",
                            value=f"Name: {teacher['first_name']} {teacher['last_name']}\nEmail: {teacher['email']}",
                            inline=False)
            await ctx.send(embed=embed)

    @commands.slash_command(description="Вивести дані з таблиці груп")
    async def show_groups(self, ctx):
        groups = await self.conn.fetch('SELECT * FROM groups')

        if not groups:
            embed = disnake.Embed(title="Помилка", description="У базі даних немає груп.", color=0xFF0000)
            await ctx.send(embed=embed)
            return

        for group in groups:
            embed = disnake.Embed(title="Group", color=0xE28CC0)
            embed.add_field(name=f"ID: {group['group_id']}", value=f"Назва: {group['name']}", inline=False)
            await ctx.send(embed=embed)

    @commands.slash_command(description="Вивести дані з таблиці предметів")
    async def show_subjects(self, ctx):
        subjects = await self.conn.fetch('SELECT * FROM subjects')

        if not subjects:
            embed = disnake.Embed(title="Помилка", description="У базі даних немає предметів.", color=0xFF0000)
            await ctx.send(embed=embed)
            return

        for subject in subjects:
            embed = disnake.Embed(title="Subject", color=0xE28CC0)
            embed.add_field(name=f"ID: {subject['subject_id']}",
                            value=f"Назва: {subject['name']}\nВикладач ID: {subject['teacher_id']}", inline=False)
            await ctx.send(embed=embed)

    @commands.slash_command(description="Вивести дані з таблиці студентів", color=0xE28CC0)
    async def show_students(self, ctx):
        students = await self.conn.fetch('SELECT * FROM students')

        if not students:
            embed = disnake.Embed(title="Помилка", description="У базі даних немає студентів.", color=0xFF0000)
            await ctx.send(embed=embed)
            return

        for student in students:
            embed = disnake.Embed(title="Student", color=0xE28CC0)
            embed.add_field(name=f"ID: {student['student_id']}",
                            value=f"Ім'я: {student['first_name']} {student['last_name']}\nEmail: {student['email']}\nГрупа ID: {student['group_id']}",
                            inline=False)
            await ctx.send(embed=embed)

    @commands.slash_command(description="Вивести дані з таблиці оцінок", color=0xE28CC0)
    async def show_grades(self, ctx):
        grades = await self.conn.fetch('SELECT * FROM grades')

        if not grades:
            embed = disnake.Embed(title="Помилка", description="У базі даних немає оцінок.", color=0xFF0000)
            await ctx.send(embed=embed)
            return

        for grade in grades:
            embed = disnake.Embed(title="Grade", color=0xE28CC0)
            embed.add_field(name=f"ID: {grade['grade_id']}",
                            value=f"Студент ID: {grade['student_id']}\nПредмет ID: {grade['subject_id']}\nОцінка: {grade['value']}",
                            inline=False)
            await ctx.send(embed=embed)

    @commands.slash_command(description="Створити розклад на неділю")
    async def create_schedule(self, ctx):
        subjects = await self.conn.fetch('SELECT * FROM subjects')
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

        embed = disnake.Embed(title="Розклад на неділю", color=0xE28CC0)

        # Отримуємо поточну дату та встановлюємо початок наступного тижня
        today = datetime.now()
        next_monday = today + timedelta(days=(7 - today.weekday()))

        for i, day in enumerate(days):
            # Випадковим чином обираємо 3-5 предметів для кожного дня
            num_subjects = random.randint(3, 5)
            selected_subjects = random.sample(subjects, num_subjects)

            # Формуємо рядок з назвами предметів для відповідного дня
            subjects_str = '\n'.join([f"{subject['name']}" for subject in selected_subjects])

            # Обчислюємо дату для поточного дня у розкладі
            current_date = next_monday + timedelta(days=i)

            embed.add_field(name=f"`{day}, {current_date.strftime('%d.%m.%Y')}`", value=subjects_str, inline=False)

        await ctx.send(embed=embed)

    @commands.slash_command(description="Вивести студентів у групі за предметом", color=0xE28CC0)
    async def show_students_in_group(self, ctx, group_name: str, subject_name: str):
        view_name = 'students_in_group_view'
        query = f'SELECT * FROM {view_name} WHERE group_name = $1 AND subject_name = $2'
        students = await self.conn.fetch(query, group_name, subject_name)

        if students:
            embed = disnake.Embed(title="Студенти в групі за предметом",
                                  description=f"Група: {group_name}, Предмет: {subject_name}", color=0xE28CC0)
            for student in students:
                embed.add_field(name=f"ID: {student['student_id']}",
                                value=f"Name: {student['first_name']} {student['last_name']}\nEmail: {student['email']}\nОцінка: {student['value']}",
                                inline=False)
            await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(title="Помилка", description="Дані не знайдені.", color=0xFF0000)
            await ctx.send(embed=embed)

    @commands.slash_command(description="Вивести середні оцінки по вибрані групі")
    async def show_average_grades_by_group(self, ctx, group_name: str):
        view_name = 'average_grades_by_group_view'
        query = f"SELECT * FROM {view_name} WHERE group_name = $1"
        average_grades = await self.conn.fetch(query, group_name)

        if average_grades:
            embed = disnake.Embed(title="Середні оцінки по групі", description=f"Група: {group_name}", color=0xE28CC0)
            for grade in average_grades:
                embed.add_field(name=f"Group ID: {grade['group_id']}",
                                value=f"Group Name: {grade['group_name']}\nAverage Grade: {grade['average_grade']}",
                                inline=False)
            await ctx.send(embed=embed)
        else:
            error_embed = disnake.Embed(title="Помилка", description=f"Група '{group_name}' не знайдена.",
                                        color=0xFF0000)
            await ctx.send(embed=error_embed)

    @commands.slash_command(description="Оновити дані про студента", color=0xE28CC0)
    @is_admin()
    async def update_student(self, ctx, student_id: int, first_name: str, last_name: str, email: str, group_id: int):
        student_data = {
            'student_id': student_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'group_id': group_id
        }

        result = await self.update_student_in_database(student_data)
        if result:  # перевіряємо, чи оновлення було успішним
            error_embed = disnake.Embed(title="Помилка", description=f"Оновити дані про студента не вдалось",
                                        color=0xFF0000)
            await ctx.send(embed=error_embed)
        else:
            embed = disnake.Embed(title="Успішно", description="Дані про студента були оновлені.", color=0x00FF00)
            await ctx.send(embed=embed)

    @commands.slash_command(description="Оновити дані про викладача", color=0xE28CC0)
    @is_admin()
    async def update_teacher(self, ctx, teacher_id: int, first_name: str, last_name: str, email: str):
        teacher_data = {
            'teacher_id': teacher_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email
        }

        result = await self.update_teacher_in_database(teacher_data)
        if result:
            error_embed = disnake.Embed(title="Помилка", description=f"Оновити дані про викладача не вдалось",
                                        color=0xFF0000)
            await ctx.send(embed=error_embed)
        else:
            embed = disnake.Embed(title="Успішно", description="Дані про викладача були оновлені.", color=0x00FF00)
            await ctx.send(embed=embed)

    async def update_teacher_in_database(self, teacher_data):
        query = """
        UPDATE Teachers
        SET first_name = $1, last_name = $2, email = $3
        WHERE teacher_id = $4
        """
        values = (
            teacher_data['first_name'],
            teacher_data['last_name'],
            teacher_data['email'],
            teacher_data['teacher_id']
        )
        await self.conn.execute(query, *values)

    @commands.slash_command(description="Оновити дані про оцінки", color=0xE28CC0)
    @is_admin()
    async def update_grade(self, ctx, grade_id: int, student_id: int, subject_id: int, value: float):
        grade_data = {
            'grade_id': grade_id,
            'student_id': student_id,
            'subject_id': subject_id,
            'value': value
        }

        result = await self.update_grade_in_database(grade_data)
        if result:
            error_embed = disnake.Embed(title="Помилка", description=f"Оновити дані про оцінки не вдалось",
                                        color=0xFF0000)
            await ctx.send(embed=error_embed)
        else:
            embed = disnake.Embed(title="Успішно", description="Дані про оцінку були оновлені.", color=0xE28CC0)
            await ctx.send(embed=embed)

    async def update_grade_in_database(self, grade_data):
        query = """
        UPDATE Grades
        SET student_id = $1, subject_id = $2, value = $3
        WHERE grade_id = $4
        """
        values = (
            grade_data['student_id'],
            grade_data['subject_id'],
            grade_data['value'],
            grade_data['grade_id']
        )
        await self.conn.execute(query, *values)

    @commands.slash_command(description="Витягнути журнал за датою (DD-MM-YYYY) (за останній рік, якщо не вказано)")
    @is_admin()
    async def show_log(self, ctx, date: str = None):
        if date:
            try:
                parsed_date = datetime.strptime(date, '%d-%m-%Y').date()
            except ValueError:
                embed = disnake.Embed(title="Помилка",
                                      description="Некоректний формат дати. Використовуйте формат DD-MM-YYYY.",
                                      color=0xFF0000)
                await ctx.send(embed=embed)
                return
        else:
            parsed_date = datetime.now().date() - timedelta(days=1)

        log_data = await self.get_log_data(parsed_date)

        if log_data:
            embed = disnake.Embed(title="Журнал", description="Отримано дані з таблиці лог.", color=0xE28CC0)

            for log_entry in log_data:
                log_date = log_entry['timestamp']
                modified_data = log_entry['old_data']
                new_data = log_entry['new_data']

                embed.add_field(name="Дата зміни", value=log_date.strftime('%d-%m-%Y %H:%M:%S'), inline=False)
                embed.add_field(name="Змінені дані", value=modified_data, inline=False)
                embed.add_field(name="Нові дані", value=new_data, inline=False)
                embed.add_field(name="------------------------------", value="\u200b", inline=False)

            await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(title="Помилка", description="Дані з таблиці лог не знайдені.", color=0xFF0000)
            await ctx.send(embed=embed)

    @commands.slash_command(description="Отримати топ-10 студентів з найвищим середнім балом")
    async def show_top_students(self, ctx):
        top_students = await self.get_top_students_data()

        if top_students:
            embed = disnake.Embed(title="Топ-10 студентів з найвищим середнім балом", color=0xE28CC0)
            for i, row in enumerate(top_students[:10]):
                student_name = row['student_name']
                average_grade = round(row['average_grade'], 1)
                embed.add_field(name=f"#{i + 1} - {student_name}", value=f"Середній бал: {average_grade}", inline=False)
            await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(title="Помилка", description="Дані про студентів не знайдені.", color=0xFF0000)
            await ctx.send(embed=embed)

    @commands.slash_command(description="Отримати оцінки студента за всі предмети")
    async def show_student_grades(self, ctx, student_id: int):
        query = f"SELECT * FROM student_grades WHERE student_id = {student_id}"
        result = await self.conn.fetch(query)

        if result:
            student_name = f"{result[0]['first_name']} {result[0]['last_name']}"
            embed = disnake.Embed(title=f"Оцінки студента {student_name}", color=0xE28CC0)
            for row in result:
                subject_name = row['subject_name']
                grade_value = row['value']
                embed.add_field(name=subject_name, value=grade_value, inline=False)
            await ctx.send(embed=embed)
        else:
            embed = disnake.Embed(title="Помилка", description="Дані про студента не знайдені.", color=0xFF0000)
            await ctx.send(embed=embed)

    @commands.slash_command(description="Отримати список студентів з середнім балом за групою")
    async def show_average_grades_students(self, ctx, group_id: int):
        query = "SELECT students.student_id, students.first_name, students.last_name, AVG(grades.value) AS average_grade " \
                "FROM students " \
                "JOIN grades ON students.student_id = grades.student_id " \
                "WHERE students.group_id = $1 " \
                "GROUP BY students.student_id, students.first_name, students.last_name"
        try:
            async with self.conn.transaction():  # Створення транзакції
                cursor = await self.conn.cursor(query, group_id)
                result = await cursor.fetch(10)
                if result:
                    embed = disnake.Embed(title="Топ-10 студентів з найвищим середнім балом", color=0xE28CC0)
                    for i, row in enumerate(result):
                        student_name = f"{row['first_name']} {row['last_name']}"
                        average_grade = round(row['average_grade'], 1)
                        embed.add_field(name=f"#{i + 1} - {student_name}", value=f"Середній бал: {average_grade}",
                                        inline=False)
                    await ctx.send(embed=embed)
                else:
                    embed = disnake.Embed(title="Помилка", description="Дані про студентів не знайдені.",
                                          color=0xFF0000)
                    await ctx.send(embed=embed)
        except Exception as e:
            # Обробка помилки
            # ...
            pass


def setup(bot):
    bot.add_cog(Database(bot))
