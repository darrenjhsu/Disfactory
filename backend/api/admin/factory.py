from datetime import datetime, timedelta

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import mark_safe

from api.models import ReportRecord, Factory, Image
from .mixins import ExportCsvMixin, RestoreMixin



class FactoryWithReportRecords(SimpleListFilter):
    title = '有舉報紀錄'
    parameter_name = 'has_report_record_within'

    def lookups(self, request, model_admin):
        return (
            ('all', '不限'),
            ('7d', '最近一週'),
            ('30d', '最近一個月'),
        )

    def queryset(self, request, queryset):
        now = datetime.now()
        if self.value() == 'all':
            factory_ids = ReportRecord.objects.only('factory_id').values('factory_id').distinct()
            factory_ids = [factory_id['factory_id'] for factory_id in factory_ids]
            queryset = queryset.filter(id__in=factory_ids)
        elif self.value() == '7d':
            factory_ids = ReportRecord.objects.only(
                'factory_id',
                'created_at',
            ).filter(created_at__range=[now - timedelta(days=7), now]).values('factory_id').distinct()
            factory_ids = [factory_id['factory_id'] for factory_id in factory_ids]
            queryset = queryset.filter(id__in=factory_ids)
        elif self.value() == '30d':
            factory_ids = ReportRecord.objects.only(
                'factory_id',
                'created_at',
            ).filter(created_at__range=[now - timedelta(days=30), now]).values('factory_id').distinct()
            factory_ids = [factory_id['factory_id'] for factory_id in factory_ids]
            queryset = queryset.filter(id__in=factory_ids)
        return queryset


class FactoryFilteredByCounty(SimpleListFilter):
    title = 'By county'
    parameter_name = 'county'
    county_mappings = [
        ('Taipei', '臺北市'),
        ('New_Taipei', '新北市'),
        ('Taoyuan', '桃園市'),
        ('Taichung', '臺中市'),
        ('Tainan', '臺南市'),
        ('Kaohsiung', '高雄市'),
        ('Yilan', '宜蘭縣'),
        ('Hsinchu_County', '新竹縣'),
        ('Hsinchu_City', '新竹市'),
        ('Miaoli', '苗栗縣'),
        ('Changhua', '彰化縣'),
        ('Nantou', '南投縣'),
        ('Yunlin', '雲林縣'),
        ('Chiayi_County', '嘉義縣'),
        ('Chiayi_City', '嘉義市'),
        ('Pingtung', '屏東縣'),
        ('Taitung', '臺東縣'),
        ('Hualien', '花蓮縣'),
        ('Penghu', '澎湖縣'),
        ('Keelung', '基隆市'),
        ('Lienchiang', '連江縣'),
        ('Kinmen', '金門縣')
    ]

    def lookups(self, _, __):
        return self.county_mappings

    def queryset(self, request, queryset):
        county_dict = dict(self.county_mappings)

        if self.value():
            county = county_dict[self.value()]
            re_str = county
            if '臺' in county:
                re_str = county.replace('臺', '(台|臺)')

            queryset = queryset.filter(townname__iregex=re_str)

        return queryset

class ReportRecordInline(admin.TabularInline):
    model = ReportRecord
    fields = (
        'created_at',
        'nickname',
        'contact',
        'others',
        'action_type',
        'action_body',
        'user_ip',
        'id',
    )
    readonly_fields = (
        'created_at',
        'nickname',
        'contact',
        'others',
        'action_type',
        'action_body',
        'user_ip',
        'id',
    )
    extra = 0


class ImageInlineForFactory(admin.TabularInline):
    model = Image
    fields = (
        'image_show',
        'created_at',
        'get_report_nickname',
        'get_report_contact',
        'id',
        'image_path',
        'report_record',
    )
    readonly_fields = (
        'id',
        'report_record',
        'image_path',
        'image_show',
        'created_at',
        'get_report_nickname',
        'get_report_contact',
    )
    extra = 0

    def get_report_contact(self, obj):
        return obj.report_record.contact

    def get_report_nickname(self, obj):
        return obj.report_record.nickname

    def image_show(self, obj):
        return mark_safe(f'<img src="{obj.image_path}" style="max-width:500px; height:auto"/>')

    image_show.short_description = 'Image Preview'
    get_report_nickname.short_description = 'Nickname'
    get_report_contact.short_description = 'Contact'


class FactoryAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = (
        'get_name',
        'created_at',
        'lat',
        'lng',
        'landcode',
        'sectcode',
        'sectname',
        'towncode',
        'townname',
        'factory_type',
        'id',
    )
    list_filter = (
        'cet_report_status',
        'source',
        'factory_type',
        FactoryWithReportRecords,
        FactoryFilteredByCounty,
    )
    ordering = ["-created_at"]
    actions = ["export_as_csv"]

    inlines = [ImageInlineForFactory, ReportRecordInline]

    def get_name(self, obj):
        return obj.name or '_'

    get_name.short_description = 'name'


class RecycledFactoryAdmin(admin.ModelAdmin, RestoreMixin):
    list_display = (
        'get_name',
        'deleted_at',
        'id',
    )

    actions = ["restore"]
    ordering = ["-deleted_at"]

    inlines = [ImageInlineForFactory, ReportRecordInline]

    def get_name(self, obj):
        return obj.name or '_'

    get_name.short_description = 'name'
