from models.base_model import BaseModel, db_factory_func

"""
This model creates lecturers model
"""


class LecturersModel(BaseModel):
    """
    Lecturer table CRUD operations.
    """
    def __init__(self, init_table=False):
        super().__init__("lecturers", {
            "id": "SERIAL PRIMARY KEY",
            "title": "VARCHAR(40) NOT NULL",
            "fname": "VARCHAR(80) NOT NULL",
            "sname": "VARCHAR(80) NOT NULL",
            "department_id": '''INT NOT NULL REFERENCES faculty(id)''',
            "email": "VARCHAR(100)"
        }, init_table=init_table)

    def addLecturer(self, data):
        """
        Adds new lecturer
        """
        return self.create(data=data)

    def listAllLecturers(self):
        """
        Returns all lecturers
        """
        return self.find(return_cols=["fname", "sname", "id"],
                         sort_by="")
    
    def listAllLecturersBySName(self):
        return self.find(return_cols=["sname"], sort_by="sname")

    @db_factory_func
    def listLecturersOfDepartment(self, conn, data):
        """
        Returns lecturers of specific department
        """
        return conn.execute('''SELECT * from lecturers where department_id= %s''' % data)

    def showALecturer(self, data):
        """
        Returns information of specific lecturer
        """
        return self.find(query="id = %s" % data['id'])

    def updateLecturer(self, data):
        return self.update_by_id(data=data, _id=data['id'])

    @db_factory_func
    def removeLecturer(self, conn, data):
        """
        Removes lecturer        
        """
        conn.execute("DELETE FROM LECTURERS WHERE id=%s" % data["id"])
