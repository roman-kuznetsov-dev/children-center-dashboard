from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum
from django.utils import timezone
from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime

from .models import SaleOrder, SaleItem
from .serializers import SaleOrderSerializer
from users.models import Club


class SaleOrderViewSet(viewsets.ModelViewSet):
    queryset = SaleOrder.objects.all().order_by('-date')
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SaleOrderSerializer

    def get_queryset(self):
        """
        Фильтрация заказов в зависимости от роли пользователя.
        - Администратор (admin) видит ВСЕ заказы.
        - Менеджер (manager) и сотрудник (staff) видят ТОЛЬКО свой клуб.
        """
        user = self.request.user

        if user.role == 'admin' or user.is_superuser:
            return SaleOrder.objects.all().order_by('-date')
        else:
            if user.club:
                return SaleOrder.objects.filter(club=user.club).order_by('-date')
            else:
                return SaleOrder.objects.none()

    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """
        Главная страница дашборда.
        Принимает start_date и end_date (YYYY-MM-DD).
        Если не переданы — берётся сегодняшний день.
        """
        user = request.user

        # Фильтрация по роли
        if user.role == 'admin' or user.is_superuser:
            orders = SaleOrder.objects.all()
        else:
            if user.club:
                orders = SaleOrder.objects.filter(club=user.club)
            else:
                orders = SaleOrder.objects.none()

        # Фильтр по дате (диапазон)
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Неверный формат даты'}, status=400)
        else:
            start_date = timezone.now().date()
            end_date = start_date

        period_orders = orders.filter(date__date__gte=start_date, date__date__lte=end_date)

        # KPI
        total_revenue = period_orders.aggregate(total=Sum('total_amount'))['total'] or 0
        total_orders = period_orders.count()
        avg_check = total_revenue / total_orders if total_orders > 0 else 0

        # Способы оплаты
        cash = period_orders.filter(payment_type='cash').aggregate(total=Sum('total_amount'))['total'] or 0
        card = period_orders.filter(payment_type='card').aggregate(total=Sum('total_amount'))['total'] or 0
        qr = period_orders.filter(payment_type='qr').aggregate(total=Sum('total_amount'))['total'] or 0

        # Категории
        period_items = SaleItem.objects.filter(order__in=period_orders)

        category_names = {
            'party': 'Праздники',
            'masterclass': 'Мастер-классы',
            'face_painting': 'Аквагрим',
            'cafe': 'Кафе',
            'toys': 'Игрушки',
            'entrance': 'Гости (входные билеты)',
        }

        categories = {}
        for key, name in category_names.items():
            categories[key] = {'name': name, 'total': 0, 'count': 0}

        for item in period_items:
            if item.category in categories:
                categories[item.category]['total'] += item.total
                categories[item.category]['count'] += item.quantity

        # Гости = проданные входные билеты (категория entrance)
        total_guests = categories.get('entrance', {}).get('count', 0)

        return Response({
            'date': f'{start_date} — {end_date}' if start_date != end_date else start_date.isoformat(),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'kpi': {
                'total_revenue': float(total_revenue),
                'total_orders': total_orders,
                'total_guests': total_guests,
                'avg_check': float(avg_check),
                'cash': float(cash),
                'card': float(card),
                'qr': float(qr),
            },
            'categories': categories,
        })

    @action(detail=False, methods=['get'])
    def clubs_comparison(self, request):
        """
        Сравнительная таблица по клубам.
        Принимает start_date и end_date (YYYY-MM-DD).
        """
        user = request.user

        # Фильтрация по роли
        if user.role == 'admin' or user.is_superuser:
            orders = SaleOrder.objects.all()
            clubs = Club.objects.all()
        else:
            if user.club:
                orders = SaleOrder.objects.filter(club=user.club)
                clubs = [user.club]
            else:
                orders = SaleOrder.objects.none()
                clubs = []

        # Фильтр по дате
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                orders = orders.filter(date__date__gte=start_date, date__date__lte=end_date)
            except ValueError:
                pass

        result = []

        for club in clubs:
            club_orders = orders.filter(club=club)
            club_items = SaleItem.objects.filter(order__in=club_orders)

            total_revenue = club_orders.aggregate(total=Sum('total_amount'))['total'] or 0
            cash = club_orders.filter(payment_type='cash').aggregate(total=Sum('total_amount'))['total'] or 0
            card = club_orders.filter(payment_type='card').aggregate(total=Sum('total_amount'))['total'] or 0
            qr = club_orders.filter(payment_type='qr').aggregate(total=Sum('total_amount'))['total'] or 0

            # Гости = входные билеты (категория entrance)
            entrance_count = club_items.filter(category='entrance').aggregate(total=Sum('quantity'))['total'] or 0

            result.append({
                'club_name': club.name,
                'total_revenue': float(total_revenue),
                'cash': float(cash),
                'card': float(card),
                'qr': float(qr),
                'total_guests': entrance_count,
                'categories': {
                    'party': club_items.filter(category='party').aggregate(total=Sum('total'))['total'] or 0,
                    'masterclass': club_items.filter(category='masterclass').aggregate(total=Sum('total'))['total'] or 0,
                    'face_painting': club_items.filter(category='face_painting').aggregate(total=Sum('total'))['total'] or 0,
                    'cafe': club_items.filter(category='cafe').aggregate(total=Sum('total'))['total'] or 0,
                    'toys': club_items.filter(category='toys').aggregate(total=Sum('total'))['total'] or 0,
                    'entrance': club_items.filter(category='entrance').aggregate(total=Sum('total'))['total'] or 0,
                },
                'categories_count': {
                    'party': club_items.filter(category='party').aggregate(total=Sum('quantity'))['total'] or 0,
                    'masterclass': club_items.filter(category='masterclass').aggregate(total=Sum('quantity'))['total'] or 0,
                    'face_painting': club_items.filter(category='face_painting').aggregate(total=Sum('quantity'))['total'] or 0,
                    'cafe': club_items.filter(category='cafe').aggregate(total=Sum('quantity'))['total'] or 0,
                    'toys': club_items.filter(category='toys').aggregate(total=Sum('quantity'))['total'] or 0,
                    'entrance': club_items.filter(category='entrance').aggregate(total=Sum('quantity'))['total'] or 0,
                }
            })

        return Response(result)

    @action(detail=False, methods=['get'])
    def export_z_report(self, request):
        """
        Экспорт Z-отчёта в Excel. Отдельный лист для каждого клуба.
        Колонки: ID, Время, Категория, Кол-во, Цена, Сумма, Оплата.
        """
        date_str = request.query_params.get('date')

        if not date_str:
            return Response({'error': 'Укажите дату в формате YYYY-MM-DD'}, status=400)

        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Неверный формат даты'}, status=400)

        user = request.user

        if user.role == 'admin' or user.is_superuser:
            clubs = Club.objects.all()
        else:
            clubs = [user.club] if user.club else []

        wb = Workbook()
        wb.remove(wb.active)

        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='3B82F6', end_color='3B82F6', fill_type='solid')
        total_font = Font(bold=True)
        total_fill = PatternFill(start_color='FEF3C7', end_color='FEF3C7', fill_type='solid')

        for club in clubs:
            sheet_name = club.name[:31]
            ws = wb.create_sheet(title=sheet_name)

            ws['A1'] = f'Z-отчёт: {club.name}'
            ws['A1'].font = Font(bold=True, size=14)
            ws['A2'] = f'Дата: {date_str}'

            # Заголовки (7 колонок)
            headers = ['ID', 'Время', 'Категория', 'Кол-во', 'Цена', 'Сумма', 'Оплата']
            for col, header in enumerate(headers, start=1):
                cell = ws.cell(row=4, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal='center')

            orders = SaleOrder.objects.filter(club=club, date__date=target_date).order_by('date')

            row = 5
            total_revenue = 0
            total_cash = 0
            total_card = 0
            total_qr = 0

            for order in orders:
                total_revenue += float(order.total_amount)
                if order.payment_type == 'cash':
                    total_cash += float(order.total_amount)
                elif order.payment_type == 'card':
                    total_card += float(order.total_amount)
                elif order.payment_type == 'qr':
                    total_qr += float(order.total_amount)

                items = order.items.all()
                if items:
                    for item in items:
                        ws.cell(row=row, column=1, value=order.id)
                        ws.cell(row=row, column=2, value=order.date.strftime('%H:%M'))
                        ws.cell(row=row, column=3, value=dict(SaleItem.CATEGORY_CHOICES).get(item.category, item.category))
                        ws.cell(row=row, column=4, value=item.quantity)
                        ws.cell(row=row, column=5, value=float(item.price))
                        ws.cell(row=row, column=6, value=float(item.total))
                        ws.cell(row=row, column=7, value=order.payment_type)
                        row += 1
                else:
                    ws.cell(row=row, column=1, value=order.id)
                    ws.cell(row=row, column=2, value=order.date.strftime('%H:%M'))
                    ws.cell(row=row, column=6, value=float(order.total_amount))
                    ws.cell(row=row, column=7, value=order.payment_type)
                    row += 1

            # Итоги
            row += 1
            ws.cell(row=row, column=6, value='ИТОГО:').font = total_font
            ws.cell(row=row, column=6).fill = total_fill
            ws.cell(row=row, column=7, value=total_revenue)
            ws.cell(row=row + 1, column=6, value='Наличные:').font = total_font
            ws.cell(row=row + 1, column=6).fill = total_fill
            ws.cell(row=row + 1, column=7, value=total_cash)
            ws.cell(row=row + 2, column=6, value='Безнал:').font = total_font
            ws.cell(row=row + 2, column=6).fill = total_fill
            ws.cell(row=row + 2, column=7, value=total_card)
            ws.cell(row=row + 3, column=6, value='QR-код:').font = total_font
            ws.cell(row=row + 3, column=6).fill = total_fill
            ws.cell(row=row + 3, column=7, value=total_qr)

            # Автоширина (7 колонок)
            for col in range(1, 8):
                ws.column_dimensions[chr(64 + col)].width = 15

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="z_report_{date_str}.xlsx"'
        wb.save(response)
        return response