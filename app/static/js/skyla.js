const Skyla = {
    async get(url) {
        const r = await fetch(url);
        if (!r.ok) throw new Error(`${r.status} ${url}`);
        return r.json();
    },

    async send(url, method = "POST", data = null) {
        const options = {
            method,
            headers: {"Content-Type": "application/json"}
        };

        if (data !== null) {
            options.body = JSON.stringify(data);
        }

        const r = await fetch(url, options);
        const result = await r.json().catch(() => ({}));

        if (!r.ok) {
            throw new Error(result.error || `${r.status} ${url}`);
        }

        return result;
    },

    esc(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    },

    toast(message, type = "success") {
        let box = document.getElementById("skyla-toast");

        if (!box) {
            box = document.createElement("div");
            box.id = "skyla-toast";
            document.body.appendChild(box);
        }

        box.className = `skyla-toast ${type}`;
        box.textContent = message;

        clearTimeout(this._toastTimer);
        this._toastTimer = setTimeout(() => {
            box.className = "skyla-toast hidden";
        }, 2500);
    },

    go(path) {
        window.location.href = path;
    }
};

window.Skyla = Skyla;
