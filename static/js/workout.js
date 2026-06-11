document.addEventListener('DOMContentLoaded', () => {
    let restTimerInterval;
    const restBanner = document.getElementById('rest-timer-banner');
    const restDisplay = document.getElementById('rest-time-display');
    const skipBtn = document.getElementById('skip-rest-btn');
    const workoutTimerNode = document.getElementById('workout-timer');
    
    const workoutDayIdInput = document.getElementById('workout_day_id');
    const workoutDayId = workoutDayIdInput ? workoutDayIdInput.value : 'unknown';
    const storageKey = `workout_draft_${workoutDayId}`;

    const getRowKey = (tr) => {
        const card = tr.closest('.exercise-card');
        if (!card) return null;
        const exerciseId = card.getAttribute('data-exercise-id');
        const td = tr.querySelector('td:first-child');
        const setNumber = td ? td.innerText.trim() : '0';
        return `${exerciseId}_${setNumber}`;
    };

    let startTimestamp = new Date().getTime();
    let totalSeconds = 0;

    const saveDraft = () => {
        const draft = {
            startTimestamp: startTimestamp,
            sets: {}
        };
        document.querySelectorAll('.set-row').forEach(tr => {
            const key = getRowKey(tr);
            if (!key) return;
            const weightInput = tr.querySelector('.weight-input');
            const repsInput = tr.querySelector('.reps-input');
            draft.sets[key] = {
                weight: weightInput ? weightInput.value : '',
                reps: repsInput ? repsInput.value : '',
                done: tr.classList.contains('done')
            };
        });
        localStorage.setItem(storageKey, JSON.stringify(draft));
    };

    // Načítanie draftu
    const draftJson = localStorage.getItem(storageKey);
    if (draftJson) {
        try {
            const draft = JSON.parse(draftJson);
            if (draft.startTimestamp) {
                startTimestamp = draft.startTimestamp;
            } else if (draft.totalSeconds) {
                startTimestamp = new Date().getTime() - (draft.totalSeconds * 1000);
            }
            
            document.querySelectorAll('.set-row').forEach(tr => {
                const key = getRowKey(tr);
                if (key && draft.sets && draft.sets[key]) {
                    const data = draft.sets[key];
                    const weightInput = tr.querySelector('.weight-input');
                    const repsInput = tr.querySelector('.reps-input');
                    const doneBtn = tr.querySelector('.done-set-btn');
                    
                    if (weightInput && data.weight !== undefined) weightInput.value = data.weight;
                    if (repsInput && data.reps !== undefined) repsInput.value = data.reps;
                    
                    if (data.done) {
                        tr.classList.add('done');
                        if (doneBtn) {
                            doneBtn.classList.replace('btn-outline-success', 'btn-success');
                            doneBtn.innerHTML = '&#8617;';
                        }
                    }
                }
            });
        } catch(e) { console.error("Chyba pri načítaní draftu:", e); }
    }

    // Globálny timer pre trvanie aktuálneho tréningu
    const updateTimer = () => {
        const now = new Date().getTime();
        totalSeconds = Math.floor((now - startTimestamp) / 1000);
        if (totalSeconds < 0) totalSeconds = 0;
        const m = String(Math.floor(totalSeconds / 60)).padStart(2, '0');
        const s = String(totalSeconds % 60).padStart(2, '0');
        if(workoutTimerNode) workoutTimerNode.innerText = `Čas: ${m}:${s}`;
    };
    updateTimer();
    setInterval(updateTimer, 1000);

    setInterval(saveDraft, 5000);

    document.querySelectorAll('.weight-input, .reps-input').forEach(input => {
        input.addEventListener('input', saveDraft);
    });

    // Audio indikácia pre odpočet ukončenia pauzy (Vibrácie pre mobil)
    const playBeep = () => {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const osc = ctx.createOscillator();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, ctx.currentTime); // A5 nota
            osc.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.3);
            if (navigator.vibrate) navigator.vibrate([200, 100, 200]);
        } catch(e) {
            console.log("Audio not supported or restricted by browser.");
        }
    };

    const startRest = (seconds) => {
        clearInterval(restTimerInterval);
        restBanner.classList.remove('d-none');
        
        let timeLeft = seconds;
        const updateDisplay = () => {
            const m = String(Math.floor(timeLeft / 60)).padStart(2, '0');
            const s = String(timeLeft % 60).padStart(2, '0');
            restDisplay.innerText = `${m}:${s}`;
        };
        
        updateDisplay();
        
        // Zvýraznenie farbou keď sa blíži čas
        restBanner.style.background = 'linear-gradient(45deg, #ffc107, #ffeb3b)';
        
        restTimerInterval = setInterval(() => {
            timeLeft--;
            
            if (timeLeft <= 10) {
                restBanner.style.background = 'linear-gradient(45deg, #dc3545, #ff6b6b)';
                restBanner.style.color = '#fff';
            }
            
            if (timeLeft <= 0) {
                clearInterval(restTimerInterval);
                restBanner.classList.add('d-none');
                playBeep();
                restBanner.style.color = '#000';
            } else {
                updateDisplay();
            }
        }, 1000);
    };

    if(skipBtn) {
        skipBtn.addEventListener('click', (e) => {
            e.preventDefault();
            clearInterval(restTimerInterval);
            restBanner.classList.add('d-none');
            restBanner.style.color = '#000';
        });
    }

    document.querySelectorAll('.done-set-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const tr = this.closest('tr');
            
            // Ak už je hotovo, zrušíme to
            if (tr.classList.contains('done')) {
                tr.classList.remove('done');
                this.classList.replace('btn-success', 'btn-outline-success');
                this.innerHTML = '&check;';
                saveDraft();
                return;
            }
            
            // Validácia povinných inputov
            const weightInput = tr.querySelector('.weight-input');
            const repsInput = tr.querySelector('.reps-input');
            
            if (!weightInput.value && weightInput.placeholder) weightInput.value = weightInput.placeholder;
            if (!repsInput.value && repsInput.placeholder) repsInput.value = repsInput.placeholder;
            
            if (!weightInput.value || !repsInput.value) {
                alert("Vyplň váhu a počet opakovaní!");
                return;
            }
            
            tr.classList.add('done');
            this.classList.replace('btn-outline-success', 'btn-success');
            this.innerHTML = '&#8617;';

            saveDraft();

            // Spustenie timeru získaného dynamicky dom elementom
            const card = tr.closest('.exercise-card');
            const restSecs = parseInt(card.getAttribute('data-rest') || '180');
            startRest(restSecs);
        });
    });

    // Uloženie logu po dokončení tréningu
    const finishBtn = document.getElementById('finish-btn');
    if (finishBtn) {
        finishBtn.addEventListener('click', () => {
            // Kontrola či je nejaká séria nezaznamenaná nedávame
            if(!confirm("Si si istý, že chceš ukončiť a uložiť tréning do databázy?")) return;
            
            finishBtn.disabled = true;
            finishBtn.innerText = 'Ukladám...';
            
            const dateInput = document.getElementById('workout-date');
            const payload = {
                workout_day_id: document.getElementById('workout_day_id').value,
                duration_seconds: totalSeconds,
                date: dateInput ? dateInput.value : null,
                sets: []
            };

            document.querySelectorAll('.set-row.done').forEach(tr => {
                const card = tr.closest('.exercise-card');
                payload.sets.push({
                    exercise_id: card.getAttribute('data-exercise-id'),
                    exercise_name: card.getAttribute('data-exercise-name'),
                    set_number: tr.querySelector('td:first-child').innerText.trim(),
                    weight: parseFloat(tr.querySelector('.weight-input').value),
                    reps: parseInt(tr.querySelector('.reps-input').value),
                    failure: false
                });
            });

            // Nebránime tréningu bez setov, ale lepšie je to chrániť
            if (payload.sets.length === 0) {
                alert("Nezaznamenal si ani jednu sériu! Pred dokončením aspoň niečo nacvakaj.");
                finishBtn.disabled = false;
                finishBtn.innerText = 'Dokončiť ✓';
                return;
            }

            fetch('/workout/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if(data.redirect) {
                    localStorage.removeItem(storageKey);
                    window.location.href = data.redirect;
                } else if(data.error) {
                    alert(data.error);
                    finishBtn.disabled = false;
                    finishBtn.innerText = 'Dokončiť ✓';
                }
            })
            .catch(err => {
                console.error(err);
                alert("Nastala chyba pri spojení so serverom.");
                finishBtn.disabled = false;
                finishBtn.innerText = 'Dokončiť ✓';
            });
        });
    }

    // Tlačidlo Zrušiť tréning
    const cancelBtn = document.getElementById('cancel-btn');
    if (cancelBtn) {
        cancelBtn.addEventListener('click', (e) => {
            e.preventDefault();
            if (confirm('Naozaj chceš zrušiť tréning? Všetky neuložené zmeny a rozpracované série sa stratia.')) {
                localStorage.removeItem(storageKey);
                window.location.href = '/workout/cancel';
            }
        });
    }
});
