document.addEventListener('DOMContentLoaded', () => {
    // Элементы DOM
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const selectBtn = document.getElementById('select-btn');
    const fileNameText = document.getElementById('file-name');
    const standardSelect = document.getElementById('standard-select');
    const checkBtn = document.getElementById('check-btn');
    
    const uploadScreen = document.getElementById('upload-screen');
    const loadingScreen = document.getElementById('loading-screen');
    const resultScreen = document.getElementById('result-screen');
    
    const downloadLink = document.getElementById('download-link');
    const backBtn = document.getElementById('back-btn');

    let currentFile = null;
    let currentSessionId = null;
    
    //  Логика выбора файла 
    selectBtn.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        handleFile(e.target.files[0]);
    });

    // Drag and Drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const file = e.dataTransfer.files[0];
        handleFile(file);
    });


    function handleFile(file) {
        if (!file) return;
        
        if (!file.name.endsWith('.docx')) {
            alert('Пожалуйста, выберите файл формата .docx');
            return;
        }

        if (file.size > 20 * 1024 * 1024) {
            alert('Файл слишком большой. Максимум 20 МБ.');
            return;
        }

        currentFile = file;
        fileNameText.textContent = file.name;
        
        standardSelect.disabled = false;
        checkBtn.classList.remove('hidden');
        selectBtn.textContent = "Выбрать другой файл";
    }

    //  Отправка на сервер 
    checkBtn.addEventListener('click', async () => {
        if (!currentFile) return;

        uploadScreen.classList.remove('active');
        loadingScreen.classList.add('active');

        const formData = new FormData();
        formData.append('file', currentFile);
        formData.append('standard', standardSelect.value);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || 'Ошибка при загрузке файла');
            }

            const resultIcon = document.getElementById('result-icon');
            const resultTitle = document.getElementById('result-title');
            const resultMessage = document.getElementById('result-message');
            
            if (data.has_issues) {
                currentSessionId = data.session_id;
                resultIcon.textContent = "⚠️";
                resultTitle.textContent = "Найдены ошибки!";
                resultMessage.textContent = `Найдено несоответствий: ${data.issues.length}. Скачайте файл, чтобы увидеть рекомендации.`;
                
                downloadLink.href = `/api/download/${data.session_id}`;
                downloadLink.classList.remove('hidden');
            } else {
                resultIcon.textContent = "✅";
                resultTitle.textContent = "Всё отлично!";
                resultMessage.textContent = 'Ошибок не найдено! Ваш документ оформлен верно.';
                
                downloadLink.classList.add('hidden');
                downloadLink.href = "#";
            }

            loadingScreen.classList.remove('active');
            resultScreen.classList.add('active');
        } catch (error) {
            console.error(error);
            alert(error.message);
            
            loadingScreen.classList.remove('active');
            uploadScreen.classList.add('active');
        }
    });

    //  Кнопка Назад
    backBtn.addEventListener('click', () => {
        resetToMainScreen();
    });

    //функция возврата на главный экран
    function resetToMainScreen(){
        currentFile = null;
        fileInput.value = '';
        fileNameText.textContent = 'Файл не выбран';
        standardSelect.disabled = true;
        checkBtn.classList.add('hidden');
        selectBtn.textContent = "Выбрать файл";

        resultScreen.classList.remove('active');
        uploadScreen.classList.add('active');
    }


    const notification = document.getElementById('notification');
    let timer = null;

    //уведомление о скачивании
    function showNotification(message, isSuccess) {
        notification.textContent = message;
        
        if (isSuccess) {
            notification.style.backgroundColor = "#2e7d32";
        } else {
            notification.style.backgroundColor = "#d32f2f";
        }

        notification.classList.add('show');
        
        clearTimeout(timer);
        timer = setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }

    // обработка клика по кнопке скачивания с проверкой ошибок
     downloadLink.addEventListener('click', async (e) => {
        e.preventDefault();
        
        const url = downloadLink.href;
        downloadLink.textContent = "Скачивание...";
        downloadLink.style.pointerEvents = "none";
        downloadLink.style.opacity = "0.7";

        try {
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error("Ошибка сервера при скачивании");
            }

            const blob = await response.blob();
            const tempUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = tempUrl;
            
            const originalName = currentFile.name.replace('.docx', ''); 
            a.download = `${originalName}_checked.docx`; 
            
            document.body.appendChild(a);
            a.click();
            
            window.URL.revokeObjectURL(tempUrl);
            document.body.removeChild(a);

            showNotification("Файл скачан успешно", true);
            resetToMainScreen();

        } catch (error) {
            console.error(error);
            showNotification("Ошибка скачивания. Попробуйте еще раз.", false);
        } finally {
            downloadLink.textContent = "Скачать файл с комментариями";
            downloadLink.style.pointerEvents = "auto";
            downloadLink.style.opacity = "1";
        }
    });
});