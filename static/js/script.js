// Tariff switcher
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    if (tabButtons.length > 0) {
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                const tab = this.getAttribute('data-tab');
                window.location.href = `/tariffs?type=${tab}`;
            });
        });
    }

     // Обработка формы обратного звонка в футере
    const callbackForm = document.querySelector('footer form');
    if (callbackForm) {
        callbackForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const phone = this.querySelector('input[name="phone"]').value;
            
            fetch('/callback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'phone': phone
                })
            })
            .then(response => {
                if (response.redirected) {
                    window.location.href = response.url;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Помилка при відправці форми. Спробуйте ще раз.');
            });
        });
    }

    // Обработка форм услуг
    const serviceForms = document.querySelectorAll('form[id^="serviceForm"]');
    serviceForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData.entries());
            const serviceId = this.getAttribute('data-service-id');
            
            fetch(`/api/submit_service_form/${serviceId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                const messageDiv = this.querySelector('.form-message') || document.getElementById('formMessage');
                if (data.success) {
                    if (messageDiv) {
                        messageDiv.textContent = data.message;
                        messageDiv.className = 'form-message success';
                    } else {
                        alert(data.message);
                    }
                    this.reset();
                } else {
                    if (messageDiv) {
                        messageDiv.textContent = data.message;
                        messageDiv.className = 'form-message error';
                    } else {
                        alert(data.message);
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Помилка при відправці форми. Спробуйте ще раз.');
            });
        });
    });

    // Обработка формы акций
    const promotionForm = document.getElementById('connectionForm');
    if (promotionForm) {
        promotionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = Object.fromEntries(formData.entries());
            
            fetch('/api/submit_promotion_form', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                const messageDiv = document.getElementById('formMessage');
                if (data.success) {
                    messageDiv.textContent = data.message;
                    messageDiv.className = 'form-message success';
                    this.reset();
                } else {
                    messageDiv.textContent = data.message;
                    messageDiv.className = 'form-message error';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Помилка при відправці форми. Спробуйте ще раз.');
            });
        });
    }

    // Обработка формы отзывов
    const reviewForm = document.getElementById('reviewForm');
    if (reviewForm) {
        reviewForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            
            fetch('/api/add_review', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert(data.message);
                    this.reset();
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Помилка при відправці відгуку. Спробуйте ще раз.');
            });
        });
    }
    
    // Chat toggle
    const chatToggle = document.getElementById('chat-toggle');
    const chatClose = document.getElementById('chat-close');
    const chatWindow = document.getElementById('chat-window');
    
    if (chatToggle && chatWindow) {
        chatToggle.addEventListener('click', function() {
            chatWindow.classList.add('active');
        });
    }
    // Chat functionality
let chatSessionId = 'chat_' + Math.random().toString(36).substr(2, 9);

function sendChatMessage() {
    const messageInput = document.querySelector('.chat-input input');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    // Добавляем сообщение в чат
    addMessageToChat(message, true);
    messageInput.value = '';
    
    // Отправляем на сервер
    fetch('/api/chat_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'message': message,
            'session_id': chatSessionId,
            'user': 'Гість'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Error sending message:', data.message);
            alert('Помилка при відправці повідомлення: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Помилка при відправці повідомлення. Спробуйте ще раз.');
    });
}

function addMessageToChat(message, isUser) {
    const chatMessages = document.querySelector('.chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'operator'}`;
    
    const p = document.createElement('p');
    p.textContent = message;
    messageDiv.appendChild(p);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Обработка отправки сообщений в чате
const chatInput = document.querySelector('.chat-input input');
if (chatInput) {
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendChatMessage();
        }
    });
}

const chatSendBtn = document.querySelector('.chat-input button');
if (chatSendBtn) {
    chatSendBtn.addEventListener('click', sendChatMessage);
}
    
    // Image lazy loading for promotions and news
    if ('IntersectionObserver' in window) {
        const lazyImages = document.querySelectorAll('img');
        
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => {
            if (img.classList.contains('lazy')) {
                imageObserver.observe(img);
            }
        });
    }
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const inputs = this.querySelectorAll('input[required], select[required], textarea[required]');
            let valid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    valid = false;
                    input.classList.add('error');
                } else {
                    input.classList.remove('error');
                }
            });
            
            if (!valid) {
                e.preventDefault();
                alert('Будь ласка, заповніть всі обов\'язкові поля');
            }
        });
    });
});
document.addEventListener('DOMContentLoaded', function() {
    // Тарифный переключатель
    const tabButtons = document.querySelectorAll('.tab-button');
    
    if (tabButtons.length > 0) {
        tabButtons.forEach(button => {
            button.addEventListener('click', function() {
                const tab = this.getAttribute('data-tab');
                window.location.href = `/tariffs?type=${tab}`;
            });
        });
    }
    
    // Чат
    const chatToggle = document.getElementById('chat-toggle');
    const chatClose = document.getElementById('chat-close');
    const chatWindow = document.getElementById('chat-window');
    
    if (chatToggle && chatWindow) {
        chatToggle.addEventListener('click', function() {
            chatWindow.classList.add('active');
        });
    }
    
    if (chatClose && chatWindow) {
        chatClose.addEventListener('click', function() {
            chatWindow.classList.remove('active');
        });
    }
    
    // Модальное окно для услуг
    const modal = document.getElementById('serviceModal');
    const closeBtn = document.querySelector('.close');
    const serviceCards = document.querySelectorAll('.service-card');
    const serviceForm = document.getElementById('serviceForm');
    const formFields = document.getElementById('formFields');
    const modalTitle = document.getElementById('modalTitle');
    const formMessage = document.getElementById('formMessage');
    
    // Открытие модального окна при клике на карточку
    serviceCards.forEach(card => {
        card.addEventListener('click', function() {
            const serviceId = this.getAttribute('data-service-id');
            loadServiceForm(serviceId);
        });
    });
    
    // Закрытие модального окна
    if (closeBtn) {
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
        });
    }
    
    // Закрытие при клике вне окна
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    // Отправка формы
    if (serviceForm) {
        serviceForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value;
            });
            
            const serviceId = serviceForm.getAttribute('data-service-id');
            
            fetch(`/submit_form/${serviceId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    formMessage.textContent = data.message;
                    formMessage.className = 'form-message success';
                    serviceForm.reset();
                    
                    // Автоматическое закрытие через 3 секунды
                    setTimeout(() => {
                        modal.style.display = 'none';
                        formMessage.textContent = '';
                        formMessage.className = 'form-message';
                    }, 3000);
                } else {
                    formMessage.textContent = data.message;
                    formMessage.className = 'form-message error';
                }
            })
            .catch(error => {
                formMessage.textContent = 'Помилка при відправці форми.';
                formMessage.className = 'form-message error';
            });
        });
    }
    
    // Загрузка формы услуги
    function loadServiceForm(serviceId) {
        fetch(`/get_service/${serviceId}`)
            .then(response => response.json())
            .then(service => {
                if (service.error) {
                    alert(service.error);
                    return;
                }
                
                modalTitle.textContent = service.form_title;
                formFields.innerHTML = '';
                formMessage.textContent = '';
                formMessage.className = 'form-message';
                
                // Создаем поля формы на основе form_fields
                service.form_fields.forEach(field => {
                    const formGroup = document.createElement('div');
                    formGroup.className = 'form-group';
                    
                    const label = document.createElement('label');
                    label.textContent = getFieldLabel(field);
                    label.htmlFor = field;
                    
                    let input;
                    
                    if (field === 'package') {
                        input = document.createElement('select');
                        input.id = field;
                        input.name = field;
                        input.required = true;
                        
                        const options = [
                            {value: 'basic', text: 'Базовий пакет'},
                            {value: 'standard', text: 'Стандартний пакет'},
                            {value: 'premium', text: 'Преміум пакет'}
                        ];
                        
                        options.forEach(opt => {
                            const option = document.createElement('option');
                            option.value = opt.value;
                            option.textContent = opt.text;
                            input.appendChild(option);
                        });
                    } else if (field === 'rooms') {
                        input = document.createElement('select');
                        input.id = field;
                        input.name = field;
                        input.required = true;
                        
                        for (let i = 1; i <= 10; i++) {
                            const option = document.createElement('option');
                            option.value = i;
                            option.textContent = i + ' кімнат';
                            input.appendChild(option);
                        }
                    } else {
                        input = document.createElement('input');
                        input.type = getInputType(field);
                        input.id = field;
                        input.name = field;
                        input.required = true;
                        input.placeholder = getFieldPlaceholder(field);
                    }
                    
                    formGroup.appendChild(label);
                    formGroup.appendChild(input);
                    formFields.appendChild(formGroup);
                });
                
                serviceForm.setAttribute('data-service-id', serviceId);
                modal.style.display = 'block';
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Помилка при завантаженні форми');
            });
    }
    
    // Вспомогательные функции для полей формы
    function getFieldLabel(field) {
        const labels = {
            'name': 'Ім\'я',
            'phone': 'Телефон',
            'email': 'Email',
            'address': 'Адреса',
            'company': 'Компанія',
            'package': 'Пакет послуг',
            'rooms': 'Кількість кімнат',
            'message': 'Повідомлення'
        };
        return labels[field] || field;
    }
    
    function getInputType(field) {
        const types = {
            'phone': 'tel',
            'email': 'email',
            'message': 'textarea'
        };
        return types[field] || 'text';
    }
    
    function getFieldPlaceholder(field) {
        const placeholders = {
            'name': 'Введіть ваше ім\'я',
            'phone': 'Введіть ваш телефон',
            'email': 'Введіть ваш email',
            'address': 'Введіть вашу адресу',
            'company': 'Введіть назву компанії',
            'message': 'Введіть ваше повідомлення'
        };
        return placeholders[field] || '';
    }
    
    // Ленивая загрузка изображений
    if ('IntersectionObserver' in window) {
        const lazyImages = document.querySelectorAll('img');
        
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => {
            if (img.classList.contains('lazy')) {
                imageObserver.observe(img);
            }
        });
    }
    
    // Валидация форм
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const inputs = this.querySelectorAll('input[required], select[required], textarea[required]');
            let valid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    valid = false;
                    input.classList.add('error');
                } else {
                    input.classList.remove('error');
                }
            });
            
            if (!valid) {
                e.preventDefault();
                alert('Будь ласка, заповніть всі обов\'язкові поля');
            }
        });
    });
});