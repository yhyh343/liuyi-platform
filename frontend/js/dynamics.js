// ===== Particle System =====
(function() {
    const canvas = document.getElementById('particle-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let particles = [];
    let mouse = { x: -1000, y: -1000 };
    
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener('resize', resize);
    
    document.addEventListener('mousemove', function(e) {
        mouse.x = e.clientX;
        mouse.y = e.clientY;
    });
    
    class Particle {
        constructor() {
            this.reset();
        }
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.size = Math.random() * 2 + 0.5;
            this.speedX = (Math.random() - 0.5) * 0.3;
            this.speedY = (Math.random() - 0.5) * 0.3;
            this.opacity = Math.random() * 0.5 + 0.1;
            this.life = Math.random() * 200 + 100;
            this.maxLife = this.life;
        }
        update() {
            this.x += this.speedX;
            this.y += this.speedY;
            this.life--;
            // Mouse interaction
            const dx = mouse.x - this.x;
            const dy = mouse.y - this.y;
            const dist = Math.sqrt(dx*dx + dy*dy);
            if (dist < 150) {
                this.x -= dx * 0.005;
                this.y -= dy * 0.005;
                this.opacity = Math.min(this.opacity + 0.02, 0.8);
            }
            if (this.life <= 0 || this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) {
                this.reset();
            }
        }
        draw() {
            const fade = this.life / this.maxLife;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(200, 168, 78, ' + (this.opacity * fade) + ')';
            ctx.fill();
        }
    }
    
    // Create particles
    const count = Math.min(80, Math.floor(canvas.width * canvas.height / 15000));
    for (let i = 0; i < count; i++) {
        particles.push(new Particle());
    }
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => { p.update(); p.draw(); });
        // Draw connections
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx*dx + dy*dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = 'rgba(200, 168, 78, ' + (0.06 * (1 - dist/120)) + ')';
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animate);
    }
    animate();
})();

// ===== Floating Ambient Particles =====
(function() {
    const container = document.querySelector('.container');
    if (!container) return;
    
    function createFloatParticle() {
        const p = document.createElement('div');
        p.className = 'float-particle';
        p.style.cssText = 'position:fixed;width:' + (Math.random()*4+2) + 'px;height:' + (Math.random()*4+2) + 'px;background:rgba(200,168,78,' + (Math.random()*0.15+0.05) + ');border-radius:50%;pointer-events:none;z-index:0;left:' + (Math.random()*100) + 'vw;top:' + (100 + Math.random()*50) + 'vh;animation:floatUp ' + (Math.random()*10+15) + 's linear forwards;';
        document.body.appendChild(p);
        setTimeout(function() { p.remove(); }, 25000);
    }
    
    // Create initial particles
    for (let i = 0; i < 15; i++) {
        setTimeout(createFloatParticle, i * 800);
    }
    setInterval(createFloatParticle, 2000);
})();

// ===== Bagua Ring Generation =====
(function() {
    const ring = document.getElementById('bagua-ring');
    if (!ring) return;
    const symbols = ['☰','☱','☲','☳','☴','☵','☶','☷'];
    symbols.forEach(function(sym, i) {
        const span = document.createElement('span');
        span.textContent = sym;
        span.style.cssText = 'position:absolute;font-size:14px;color:rgba(200,168,78,0.25);top:50%;left:50%;transform-origin:0 0;';
        const angle = (i / 8) * Math.PI * 2;
        const r = 58;
        span.style.transform = 'translate(-50%,-50%) rotate(' + (angle * 180 / Math.PI) + 'deg) translate(' + r + 'px) rotate(-' + (angle * 180 / Math.PI) + 'deg)';
        ring.appendChild(span);
    });
})();

// ===== Scroll Reveal Animation =====
(function() {
    const cards = document.querySelectorAll('.step-card');
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });
    
    cards.forEach(function(card) {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
})();

// ===== Progress Track Update =====
(function() {
    const dots = document.querySelectorAll('.progress-dot');
    const lineFill = document.getElementById('progress-line-fill');
    let currentStep = 1;
    
    window.updateProgress = function(step) {
        currentStep = step;
        dots.forEach(function(dot, i) {
            dot.classList.toggle('active', i < step);
        });
        if (lineFill && dots.length > 0) {
            const firstDot = dots[0];
            const lastDot = dots[dots.length - 1];
            const totalWidth = lastDot.offsetLeft - firstDot.offsetLeft;
            const progress = ((step - 1) / (dots.length - 1)) * totalWidth;
            lineFill.style.width = progress + 'px';
        }
    };
})();
