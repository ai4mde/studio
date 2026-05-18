from django.core.management.base import BaseCommand
from metadata.models import Interface


class Command(BaseCommand):
    """为所有现有 Interface 的 sections 补上 position 字段（默认 main）"""
    
    help = "为现有 Interface 的 sections 补上 position 字段"

    def handle(self, *args, **options):
        total_interfaces = Interface.objects.count()
        updated_count = 0
        section_updated_count = 0
        
        self.stdout.write(f"开始迁移，共 {total_interfaces} 个 Interface...")
        
        for interface in Interface.objects.all():
            data = interface.data or {}
            sections = data.get('sections', [])
            
            interface_changed = False
            for section in sections:
                # 如果没有 position，默认赋 "main"
                if 'position' not in section:
                    section['position'] = 'main'
                    interface_changed = True
                    section_updated_count += 1
            
            if interface_changed:
                interface.data = data
                interface.save()
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f"✓ 更新 Interface: {interface.name}"))
        
        self.stdout.write(self.style.SUCCESS(f"\n迁移完成！"))
        self.stdout.write(f"修改了 {updated_count} 个 Interface")
        self.stdout.write(f"补充了 {section_updated_count} 个 Section 的 position 字段")
