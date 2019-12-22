from django.shortcuts import render
from django.http import FileResponse
from .models import Sensor, SensorCategory, AtmoSnapshot
from django.views.generic import CreateView
from django.forms.models import model_to_dict
import datetime
import csv
from odf.opendocument import OpenDocumentText
from odf.style import Style, TextProperties
from odf.text import H, P, Span


def index(request):
    return render(request, "index.html")

def sensor(request, id):
    sensor = Sensor.objects.filter(id=id).values()
    category = SensorCategory.objects.filter(id=list(sensor)[0]['category_id']).values()
    return render(request, "sensor.html", context={"sensor": list(sensor)[0], "category": list(category)[0]})

def sensors(request):
    sensors = Sensor.objects.all()
    return render(request, "sensors.html", context={"sensors": list(sensors)})

def exports(request):
    return render(request, "exports.html")

def export_csv(request):
    try:
        exporter = Exporter()
        exporter.export_to_csv(get_data())
        return render(request, "success.html", context={"data": 'csv'})
    except Exception:
        return render(request, "fail.html", context={"data": 'csv'})

def export_odt(request):
    try:
        exporter = Exporter()
        exporter.export_to_odt(get_data())
        return render(request, "success.html", context={"data": 'odt'})
    except Exception:
        return render(request, "fail.html", context={"data": 'odt'})

def success(request, data):
    return render(request, "success.html", context={"data": data})

def get_csv(request):
    try:
        return render(request, 'formated_data\\data.csv', content_type='text/csv')
    except Exception:
        return render(request, "fail.html", context={"data": 'csv_get'})

def get_odt(request):
    try:
        return FileResponse(open('templates\\formated_data\\data.odt', 'rb'))
    except Exception:
        return render(request, "fail.html", context={"data": 'odt_get'})

class SensorCategoryCreateView(CreateView):
    template_name = 'creations/sensor_category_create.html'
    success_url="/success/sensor_category/"
    model = SensorCategory
    fields = ('name',)

class SensorCreateView(CreateView):
    template_name = 'creations/sensor_create.html'
    success_url="/success/sensor/"
    model = Sensor
    fields = ('lon', 'lat', 'create_date', 'name', 'model', 'category',)

class AtmoSnapshotCreateView(CreateView):
    template_name = 'creations/snapshot_create.html'
    success_url="/success/snapshot/"
    model = AtmoSnapshot
    fields = ('temperature', 'pressure', 'co2_level', 'sensor',)




def get_data():
    data_model = ModelData()
    sensor_categories = SensorCategory.objects.all()
    sensors = Sensor.objects.all()
    snapshots = AtmoSnapshot.objects.all()
    data_model.add_data(sensor_categories, "Sensor Categories")
    data_model.add_data(sensors, "Sensors")
    data_model.add_data(snapshots, "Snapshots")
    data_model.map("Sensors", "Sensor Categories", "category", "name")
    data_model.map("Snapshots", "Sensors", "sensor", "name")
    return data_model.get_data()

class Exporter(object):

    def export_to_csv(self, data):
        file = open('templates\\formated_data\\data.csv', 'w')
        for k, v in data.items():
            writer = csv.writer(file)
            writer.writerow([k])
            columns = [k for k in v[0].keys()]
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(v)
        file.close()

    def export_to_odt(self, data):
        document = OpenDocumentText()
        # Styles
        s = document.styles
        h1style = Style(name="Heading 1", family="paragraph")
        h1style.addElement(TextProperties(attributes={'fontsize':"24pt",'fontweight':"bold" }))
        s.addElement(h1style)

        h2style = Style(name="Heading 2", family="paragraph")
        h2style.addElement(TextProperties(attributes={'fontsize':"16pt",'fontweight':"bold" }))
        s.addElement(h2style)

        h3style = Style(name="Heading 3", family="paragraph")
        h3style.addElement(TextProperties(attributes={'fontsize':"12pt",'fontweight':"bold" }))
        s.addElement(h3style)

        h4style = Style(name="Heading 4", family="paragraph")
        h4style.addElement(TextProperties(attributes={'fontsize':"8pt" }))
        s.addElement(h4style)
        # Text
        h=H(outlinelevel=1, stylename=h1style, text="Data of AtmoStation")
        document.text.addElement(h)
        h=H(outlinelevel=1, stylename=h2style, text=str(datetime.datetime.now()))
        document.text.addElement(h)
        for k, v in data.items():
            h=H(outlinelevel=1, stylename=h2style, text=k)
            document.text.addElement(h)
            for v1 in v:
                h=H(outlinelevel=2, stylename=h3style, text="Item")
                document.text.addElement(h)
                for v2 in v1:
                    h=H(outlinelevel=3, stylename=h4style, text=str(v2) + ": " + str(v1[v2]))
                    document.text.addElement(h)

        document.save('templates\\formated_data\\data.odt')

class ModelData(object):
    def __init__(self):
        self.data = {}

    def add_data(self, data, name):
        self.__convert_to_dict(data, name)

    def set_data(self, data):
        self.data = data

    def get_data(self):
        return self.data

    def map(self, name_data1, name_data2, filed_cmp, field_fill):
        for d in self.data[name_data1]:
            d[filed_cmp] = next(d2 for d2 in self.data[name_data2] if d2["id"]==d[filed_cmp])[field_fill]

    def __convert_to_dict(self, data, name):
        cur_data = []
        for d in data:
            cur_data.append(model_to_dict(d))
        self.data[name] = cur_data