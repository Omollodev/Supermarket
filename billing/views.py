from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import qrcode
import io
import base64
from .models import Invoice, InvoiceItem, Customer, Payment, AccountsReceivable, AccountsPayable
from .forms import InvoiceForm, InvoiceItemForm, CustomerForm, PaymentForm

@login_required
def billing_dashboard(request):
    # Get billing statistics
    today = timezone.now().date()
    this_month = timezone.now().replace(day=1).date()
    
    stats = {
        'today_sales': Invoice.objects.filter(created_at__date=today).aggregate(
            total=Sum('total_amount'))['total'] or 0,
        'monthly_sales': Invoice.objects.filter(created_at__date__gte=this_month).aggregate(
            total=Sum('total_amount'))['total'] or 0,
        'pending_invoices': Invoice.objects.filter(payment_status='pending').count(),
        'overdue_invoices': Invoice.objects.filter(payment_status='overdue').count(),
    }
    
    # Recent invoices
    recent_invoices = Invoice.objects.all()[:10]
    
    # Accounts receivable
    accounts_receivable = AccountsReceivable.objects.filter(is_settled=False)[:5]
    
    context = {
        'stats': stats,
        'recent_invoices': recent_invoices,
        'accounts_receivable': accounts_receivable,
    }
    
    return render(request, 'billing/dashboard.html', context)

@login_required
def create_invoice(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.staff_member = request.user
            invoice.save()
            messages.success(request, f'Invoice {invoice.invoice_number} created successfully!')
            return redirect('edit_invoice', invoice_id=invoice.id)
    else:
        form = InvoiceForm()
    
    return render(request, 'billing/create_invoice.html', {'form': form})

@login_required
def edit_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        if 'add_item' in request.POST:
            item_form = InvoiceItemForm(request.POST)
            if item_form.is_valid():
                item = item_form.save(commit=False)
                item.invoice = invoice
                item.save()
                messages.success(request, 'Item added successfully!')
                return redirect('edit_invoice', invoice_id=invoice.id)
        elif 'update_invoice' in request.POST:
            form = InvoiceForm(request.POST, instance=invoice)
            if form.is_valid():
                form.save()
                messages.success(request, 'Invoice updated successfully!')
                return redirect('edit_invoice', invoice_id=invoice.id)
    
    form = InvoiceForm(instance=invoice)
    item_form = InvoiceItemForm()
    
    context = {
        'invoice': invoice,
        'form': form,
        'item_form': item_form,
    }
    
    return render(request, 'billing/edit_invoice.html', context)

@login_required
def delete_invoice_item(request, item_id):
    item = get_object_or_404(InvoiceItem, id=item_id)
    invoice_id = item.invoice.id
    item.delete()
    messages.success(request, 'Item deleted successfully!')
    return redirect('edit_invoice', invoice_id=invoice_id)

@login_required
def invoice_list(request):
    invoices = Invoice.objects.all()
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        invoices = invoices.filter(payment_status=status)
    
    # Filter by date range
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date:
        invoices = invoices.filter(created_at__date__gte=start_date)
    if end_date:
        invoices = invoices.filter(created_at__date__lte=end_date)
    
    context = {
        'invoices': invoices,
        'status': status,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'billing/invoice_list.html', context)

@login_required
def invoice_detail(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    # Generate QR code for payment
    qr_data = f"Invoice: {invoice.invoice_number}\nAmount: ${invoice.total_amount}\nDue: {invoice.due_date.strftime('%Y-%m-%d')}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    qr_img.save(buffer, format='PNG')
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    context = {
        'invoice': invoice,
        'qr_code': qr_code_base64,
    }
    
    return render(request, 'billing/invoice_detail.html', context)

@login_required
def add_payment(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()
            messages.success(request, f'Payment of ${payment.amount} added successfully!')
            return redirect('invoice_detail', invoice_id=invoice.id)
    else:
        form = PaymentForm()
    
    context = {
        'invoice': invoice,
        'form': form,
    }
    
    return render(request, 'billing/add_payment.html', context)

@login_required
def generate_receipt(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{invoice.invoice_number}.pdf"'
    
    # Create PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Header
    story.append(Paragraph("SUPERMARKET RECEIPT", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Invoice details
    invoice_data = [
        ['Invoice Number:', invoice.invoice_number],
        ['Date:', invoice.created_at.strftime('%Y-%m-%d %H:%M')],
        ['Customer:', invoice.customer.name if invoice.customer else 'Walk-in Customer'],
        ['Staff:', invoice.staff_member.get_full_name()],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[2*72, 4*72])
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(invoice_table)
    story.append(Spacer(1, 12))
    
    # Items
    items_data = [['Description', 'Qty', 'Unit Price', 'Total']]
    for item in invoice.items.all():
        items_data.append([
            item.description,
            str(item.quantity),
            f'${item.unit_price}',
            f'${item.total_price}'
        ])
    
    items_table = Table(items_data, colWidths=[3*72, 1*72, 1.5*72, 1.5*72])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(items_table)
    story.append(Spacer(1, 12))
    
    # Totals
    totals_data = [
        ['Subtotal:', f'${invoice.subtotal}'],
        ['Tax ({invoice.tax_rate}%):', f'${invoice.tax_amount}'],
        ['Discount:', f'${invoice.discount_amount}'],
        ['Total:', f'${invoice.total_amount}'],
        ['Paid:', f'${invoice.paid_amount}'],
        ['Balance:', f'${invoice.total_amount - invoice.paid_amount}'],
    ]
    
    totals_table = Table(totals_data, colWidths=[4*72, 2*72])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -2), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(totals_table)
    
    doc.build(story)
    return response

@login_required
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'billing/customer_list.html', {'customers': customers})

@login_required
def create_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer {customer.name} created successfully!')
            return redirect('customer_list')
    else:
        form = CustomerForm()
    
    return render(request, 'billing/create_customer.html', {'form': form})

@login_required
def accounts_receivable_view(request):
    receivables = AccountsReceivable.objects.filter(is_settled=False)
    return render(request, 'billing/accounts_receivable.html', {'receivables': receivables})

@login_required
def accounts_payable_view(request):
    payables = AccountsPayable.objects.filter(is_paid=False)
    return render(request, 'billing/accounts_payable.html', {'payables': payables})
