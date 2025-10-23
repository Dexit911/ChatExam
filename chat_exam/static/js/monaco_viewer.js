// Used for inspection of code
function initMonacoViewer(files, containerId = "editor", tabBarId = "tab-bar") {
    require.config({ paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs" } });
    require(["vs/editor/editor.main"], function () {
        console.log("✅ Loaded files:", files);

        const tabBar = document.getElementById(tabBarId);
        const editorContainer = document.getElementById(containerId);

        if (!files || Object.keys(files).length === 0) {
            editorContainer.innerHTML = "<p style='padding:20px;color:#aaa;'>No files to display</p>";
            return;
        }

        const firstFile = Object.keys(files)[0];
        const editor = monaco.editor.create(editorContainer, {
            value: files[firstFile],
            language: detectLanguage(firstFile),
            theme: "vs-dark",
            readOnly: true,
            fontSize: 15,
            minimap: { enabled: false },
            scrollBeyondLastLine: false
        });

        Object.keys(files).forEach((name, i) => {
            const tab = document.createElement("div");
            tab.id = `tab-${name}`;
            tab.className = "tab" + (i === 0 ? " active" : "");
            tab.innerText = name;
            tab.onclick = () => setActiveTab(name);
            tabBar.appendChild(tab);
        });

        function setActiveTab(tabName) {
            const lang = detectLanguage(tabName);
            monaco.editor.setModelLanguage(editor.getModel(), lang);
            editor.setValue(files[tabName]);
            document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
            document.getElementById(`tab-${tabName}`).classList.add("active");
        }

        function detectLanguage(filename) {
            const ext = filename.split(".").pop();
            return { html: "html", css: "css", js: "javascript", py: "python" }[ext] || "plaintext";
        }
    });
}
