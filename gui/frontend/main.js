let createExceptions = [];
let createWildcards = [];
let editingJobId = null;

fetch("/api/initial-data")
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error: ${response.status}`);
        }

        return response.json();
    })
    .then(data => {

        data.jobs = data.jobs.filter(
            job => job.source !== "DELETED"
        );

        console.log("Initial data:", data);

        document.querySelector(".ver").textContent =
            "Version: " + data.version;

        document.querySelector(".store").textContent =
            data.storage + "% of backup drive full";

        document.querySelector(".total").textContent =
            "Total Jobs: " + data.jobs.length;


        function renderJobs(jobList, showNoJobsMessage = false) {

            const jobs = document.querySelector(".jobs");

            jobs.innerHTML = "";

            if (jobList.length === 0) {

                if (showNoJobsMessage) {

                    const noJobs = document.createElement("p");

                    noJobs.className = "nojob";
                    noJobs.textContent = "No Backup Jobs Found.";

                    jobs.appendChild(noJobs);
                }

                return;
            }


            jobList.forEach(job => {

                const card = document.createElement("div");
                card.className = "job-card";


                const header = document.createElement("div");
                header.className = "job-card-header";


                const jobId = document.createElement("p");
                jobId.className = "job-id";
                jobId.textContent = "Job Id: " + job.job_id;


                const actions = document.createElement("div");
                actions.className = "job-actions";


                const editButton = document.createElement("button");
                editButton.className = "job-edit";
                editButton.type = "button";
                editButton.dataset.jobId = job.job_id;


                const editIcon = document.createElement("img");
                editIcon.src = "/gui/assets/Edit icon.svg";
                editIcon.alt = "Edit";


                editButton.appendChild(editIcon);


                const deleteButton = document.createElement("button");
                deleteButton.className = "job-delete";
                deleteButton.type = "button";
                deleteButton.dataset.jobId = job.job_id;


                const deleteIcon = document.createElement("img");
                deleteIcon.src = "/gui/assets/Delete icon.svg";
                deleteIcon.alt = "Delete";


                deleteButton.appendChild(deleteIcon);


                actions.appendChild(editButton);
                actions.appendChild(deleteButton);

                header.appendChild(jobId);
                header.appendChild(actions);


                const separator = document.createElement("div");
                separator.className = "job-separator";


                const info = document.createElement("div");
                info.className = "job-info";


                function addInfo(title, value, iconPath) {

                    const item = document.createElement("div");
                    item.className = "job-info-item";


                    const iconBox = document.createElement("div");
                    iconBox.className = "job-icon";


                    const icon = document.createElement("img");
                    icon.className = "job-icon-image";
                    icon.src = iconPath;
                    icon.alt = "";


                    iconBox.appendChild(icon);


                    const text = document.createElement("div");
                    text.className = "job-info-text";


                    const titleElement = document.createElement("p");
                    titleElement.className = "job-info-title";
                    titleElement.textContent = title;


                    const valueElement = document.createElement("p");
                    valueElement.className = "job-info-value";
                    valueElement.textContent = value;


                    text.appendChild(titleElement);
                    text.appendChild(valueElement);

                    item.appendChild(iconBox);
                    item.appendChild(text);

                    info.appendChild(item);
                }


                let exceptions = [];

                try {
                    exceptions = JSON.parse(job.exceptions);
                }
                catch {
                    exceptions = [];
                }


                const exceptionText =
                    exceptions.length > 0
                        ? exceptions.join(", ")
                        : "None";


                addInfo(
                    "Source",
                    job.source,
                    "/gui/assets/Folder Icon.svg"
                );


                addInfo(
                    "Destination",
                    job.destination,
                    "/gui/assets/Folder Icon.svg"
                );


                addInfo(
                    "Time Period",
                    job.time,
                    "/gui/assets/Clock icon.svg"
                );


                addInfo(
                    "Exceptions",
                    exceptionText,
                    "/gui/assets/Exceptions icon.svg"
                );


                addInfo(
                    "Archiving",
                    job.zip,
                    "/gui/assets/Archive icon.svg"
                );


                card.appendChild(header);
                card.appendChild(separator);
                card.appendChild(info);

                jobs.appendChild(card);


                editButton.addEventListener("click", () => {

                    openEditJob(job);

                });


                deleteButton.addEventListener("click", async () => {

                    const confirmed = confirm(
                        `Are you sure you want to delete Job ${job.job_id}?`
                    );

                    if (!confirmed) {
                        return;
                    }


                    try {

                        const response = await fetch(
                            `/api/jobs/${job.job_id}`,
                            {
                                method: "DELETE"
                            }
                        );


                        const result =
                            await response.json();


                        if (!response.ok) {

                            throw new Error(
                                result.error ||
                                "Failed to delete job."
                            );

                        }


                        data.jobs = data.jobs.filter(
                            existingJob =>
                                existingJob.job_id !== job.job_id
                        );


                        document.querySelector(".total")
                            .textContent =
                                "Total Jobs: " +
                                data.jobs.length;


                        renderJobs(
                            data.jobs,
                            true
                        );

                    }
                    catch (error) {

                        console.error(
                            "Failed to delete job:",
                            error
                        );

                    }

                });

            });

        }


        renderJobs(data.jobs, true);


        const jobSearch =
            document.querySelector("#job-id-search");


        jobSearch.addEventListener("input", () => {

            jobSearch.value =
                jobSearch.value.replace(/\D/g, "");

        });


        jobSearch.addEventListener("keydown", event => {

            if (event.key !== "Enter") {
                return;
            }


            if (jobSearch.value === "") {

                renderJobs(data.jobs, true);

                return;
            }


            const id =
                Number(jobSearch.value);


            const matchingJob =
                data.jobs.find(
                    job => job.job_id === id
                );


            if (matchingJob) {

                renderJobs([
                    matchingJob
                ]);

            }
            else {

                renderJobs([]);

            }

        });


        const settingsButton =
            document.querySelector("#settings-button");

        const settingsOverlay =
            document.querySelector("#settings-overlay");


        settingsButton.addEventListener("click", () => {

            settingsOverlay.style.display = "flex";


            fetch("/api/settings")
                .then(response => {

                    if (!response.ok) {
                        throw new Error(
                            `HTTP error: ${response.status}`
                        );
                    }

                    return response.json();

                })
                .then(settings => {

                    document.querySelector(
                        "#setting-backuploc"
                    ).value =
                        settings.backuploc;


                    const timeMatch =
                        settings.time.match(
                            /^(\d+)(mm|m|h|d)$/
                        );


                    if (timeMatch) {

                        document.querySelector(
                            "#setting-time"
                        ).value =
                            timeMatch[1];


                        document.querySelector(
                            "#setting-time-unit"
                        ).value =
                            timeMatch[2];

                    }


                    document.querySelector(
                        "#setting-zip"
                    ).checked =
                        settings.zip;


                    document.querySelector(
                        "#setting-logging"
                    ).checked =
                        settings.logging;


                    document.querySelector(
                        "#autorun-toggle"
                    ).textContent =
                        settings.autorun
                            ? "Stop backup script autorun"
                            : "Start backup script autorun";

                })
                .catch(error => {

                    console.error(
                        "Failed to get settings:",
                        error
                    );

                });

        });


        document.querySelector("#settings-save")
            .addEventListener("click", () => {

                const settings = {

                    backuploc:
                        document.querySelector(
                            "#setting-backuploc"
                        ).value,

                    timeperiod:
                        document.querySelector(
                            "#setting-time"
                        ).value +
                        document.querySelector(
                            "#setting-time-unit"
                        ).value,

                    zip:
                        document.querySelector(
                            "#setting-zip"
                        ).checked,

                    logging:
                        document.querySelector(
                            "#setting-logging"
                        ).checked

                };


                fetch("/api/settings", {

                    method: "PUT",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body:
                        JSON.stringify(settings)

                })
                    .then(response => {

                        if (!response.ok) {
                            throw new Error(
                                `HTTP error: ${response.status}`
                            );
                        }

                        return response.json();

                    })
                    .then(result => {

                        console.log(
                            "Settings saved:",
                            result
                        );

                        settingsOverlay.style.display =
                            "none";

                    })
                    .catch(error => {

                        console.error(
                            "Failed to save settings:",
                            error
                        );

                    });

            });


        document.querySelector("#autorun-toggle")
            .addEventListener("click", async () => {

                const button =
                    document.querySelector(
                        "#autorun-toggle"
                    );


                try {

                    const settingsResponse =
                        await fetch(
                            "/api/settings"
                        );


                    if (!settingsResponse.ok) {
                        throw new Error(
                            `HTTP error: ${settingsResponse.status}`
                        );
                    }


                    const settings =
                        await settingsResponse.json();


                    const newValue =
                        !settings.autorun;


                    const response =
                        await fetch(
                            "/api/autorun",
                            {
                                method: "PUT",

                                headers: {
                                    "Content-Type":
                                        "application/json"
                                },

                                body:
                                    JSON.stringify({
                                        autorun: newValue
                                    })
                            }
                        );


                    const result =
                        await response.json();


                    if (!response.ok) {
                        throw new Error(
                            result.error ||
                            "Failed to change autorun."
                        );
                    }


                    button.textContent =
                        result.autorun
                            ? "Stop backup script autorun"
                            : "Start backup script autorun";

                }
                catch (error) {

                    console.error(
                        "Failed to change autorun:",
                        error
                    );

                }

            });


        document.querySelector("#delete-all")
            .addEventListener("click", () => {

                const confirmed = confirm(
                    "Are you sure you want to delete all backup jobs?"
                );


                if (!confirmed) {
                    return;
                }


                fetch("/api/jobs", {
                    method: "DELETE"
                })
                    .then(response => {

                        if (!response.ok) {
                            throw new Error(
                                `HTTP error: ${response.status}`
                            );
                        }

                        return response.json();

                    })
                    .then(result => {

                        console.log(
                            "All jobs deleted:",
                            result
                        );

                        data.jobs = [];

                        document.querySelector(".total")
                            .textContent =
                                "Total Jobs: 0";

                        renderJobs(
                            [],
                            true
                        );

                    })
                    .catch(error => {

                        console.error(
                            "Failed to delete all jobs:",
                            error
                        );

                    });

            });


        settingsOverlay.addEventListener(
            "click",
            event => {

                if (event.target === settingsOverlay) {
                    settingsOverlay.style.display = "none";
                }

            }
        );


        const createButton =
            document.querySelector("#create-button");

        const createOverlay =
            document.querySelector("#create-overlay");

        const createError =
            document.querySelector("#create-error");


        function clearCreateError() {

            createError.textContent = "";
            createError.style.display = "none";

        }


        function showCreateError(message) {

            createError.textContent = message;
            createError.style.display = "block";

        }


        function resetCreateForm() {

            document.querySelector("#create-source")
                .value = "";

            document.querySelector("#create-destination")
                .value = "";

            document.querySelector("#create-time")
                .value = "";

            document.querySelector("#create-time-unit")
                .value = "m";

            document.querySelector("#create-wildcards")
                .value = "";

            document.querySelector("#create-zip")
                .checked = false;

            createExceptions = [];
            createWildcards = [];

            displayExceptions();

            clearCreateError();

        }


        function displayExceptions() {

            const list =
                document.querySelector(
                    "#create-exceptions-list"
                );


            const input =
                document.querySelector(
                    "#create-exceptions"
                );


            list.innerHTML = "";


            if (createExceptions.length === 0) {

                input.value = "";

                return;

            }


            input.value =
                createExceptions.length === 1
                    ? "1 file selected"
                    : `${createExceptions.length} files selected`;


            createExceptions.forEach((path, index) => {

                const item =
                    document.createElement("div");

                item.className =
                    "create-exception";


                const name =
                    document.createElement("span");

                name.textContent =
                    path.split(/[/\\]/).pop();


                const remove =
                    document.createElement("button");

                remove.type = "button";
                remove.textContent = "×";


                remove.addEventListener(
                    "click",
                    () => {

                        createExceptions.splice(
                            index,
                            1
                        );

                        displayExceptions();

                    }
                );


                item.appendChild(name);
                item.appendChild(remove);

                list.appendChild(item);

            });

        }


        function validWildcard(pattern) {

            pattern = pattern.trim();


            if (!pattern) {
                return false;
            }


            if (
                !pattern.includes("*") &&
                !pattern.includes("?") &&
                !pattern.includes("[")
            ) {
                return false;
            }


            if (
                pattern.includes("/") ||
                pattern.includes("\\")
            ) {
                return false;
            }


            if (
                pattern.includes("[") &&
                !pattern.includes("]")
            ) {
                return false;
            }


            return true;

        }


        async function browsePath(mode, inputSelector) {

            try {

                const response =
                    await fetch(
                        "/api/browse",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                mode: mode
                            })
                        }
                    );


                if (!response.ok) {
                    throw new Error(
                        `HTTP error: ${response.status}`
                    );
                }


                const result =
                    await response.json();


                if (
                    result.path === null ||
                    result.path === undefined ||
                    result.path === "" ||
                    (
                        Array.isArray(result.path) &&
                        result.path.length === 0
                    )
                ) {
                    return;
                }


                if (mode === "files") {

                    if (!Array.isArray(result.path)) {
                        return;
                    }


                    result.path.forEach(path => {

                        if (
                            !createExceptions.includes(path)
                        ) {

                            createExceptions.push(
                                path
                            );

                        }

                    });


                    displayExceptions();

                    return;

                }


                document.querySelector(
                    inputSelector
                ).value = result.path;

            }
            catch (error) {

                console.error(
                    "Failed to select path:",
                    error
                );

            }

        }


        document.querySelectorAll(
            ".browse-folder, .browse-path"
        ).forEach(button => {

            button.addEventListener("click", () => {

                const mode =
                    button.dataset.mode || "folder";


                browsePath(
                    mode,
                    button.dataset.target
                );

            });

        });


        function openCreateMode() {

            editingJobId = null;

            resetCreateForm();

            document.querySelector(
                ".create-panel h1"
            ).textContent = "Create Job";


            document.querySelector(
                "#create-job"
            ).textContent = "Create Job";


            createOverlay.style.display =
                "flex";


            fetch("/api/settings")
                .then(response => {

                    if (!response.ok) {
                        throw new Error(
                            `HTTP error: ${response.status}`
                        );
                    }

                    return response.json();

                })
                .then(settings => {

                    document.querySelector(
                        "#create-destination"
                    ).value =
                        settings.backuploc;


                    const timeMatch =
                        settings.time.match(
                            /^(\d+)(mm|m|h|d)$/
                        );


                    if (timeMatch) {

                        document.querySelector(
                            "#create-time"
                        ).value =
                            timeMatch[1];


                        document.querySelector(
                            "#create-time-unit"
                        ).value =
                            timeMatch[2];

                    }


                    document.querySelector(
                        "#create-zip"
                    ).checked =
                        settings.zip;

                })
                .catch(error => {

                    console.error(
                        "Failed to get Create Job defaults:",
                        error
                    );

                });

        }


        function openEditJob(job) {

            editingJobId =
                job.job_id;


            clearCreateError();

            createOverlay.style.display =
                "flex";


            document.querySelector(
                ".create-panel h1"
            ).textContent =
                "Edit Job";


            document.querySelector(
                "#create-job"
            ).textContent =
                "Save Changes";


            document.querySelector(
                "#create-source"
            ).value =
                job.source;


            document.querySelector(
                "#create-destination"
            ).value =
                job.destination;


            const timeMatch =
                job.time.match(
                    /^(\d+)(mm|m|h|d)$/
                );


            if (timeMatch) {

                document.querySelector(
                    "#create-time"
                ).value =
                    timeMatch[1];


                document.querySelector(
                    "#create-time-unit"
                ).value =
                    timeMatch[2];

            }


            document.querySelector(
                "#create-zip"
            ).checked =
                job.zip === "Yes";


            createExceptions = [];
            createWildcards = [];


            let storedExceptions = [];


            try {

                storedExceptions =
                    JSON.parse(job.exceptions);

            }
            catch {

                storedExceptions = [];

            }


            storedExceptions.forEach(item => {

                if (
                    typeof item !== "string"
                ) {
                    return;
                }


                if (
                    item.includes("*") ||
                    item.includes("?") ||
                    (
                        item.includes("[") &&
                        item.includes("]")
                    )
                ) {

                    createWildcards.push(
                        item
                    );

                    return;
                }


                if (
                    job.source &&
                    !job.source.includes("\0")
                ) {

                    createExceptions.push(
                        job.source +
                        "\\" +
                        item
                    );

                }

            });


            displayExceptions();


            document.querySelector(
                "#create-wildcards"
            ).value =
                createWildcards.join(", ");

        }


        createButton.addEventListener(
            "click",
            openCreateMode
        );


        document.querySelector(
            "#create-cancel"
        )
            .addEventListener(
                "click",
                () => {

                    createOverlay.style.display =
                        "none";

                    editingJobId = null;

                    resetCreateForm();

                }
            );


        createOverlay.addEventListener(
            "click",
            event => {

                if (
                    event.target ===
                    createOverlay
                ) {

                    createOverlay.style.display =
                        "none";

                    editingJobId = null;

                    resetCreateForm();

                }

            }
        );


        document.querySelector(
            "#create-wildcards"
        )
            .addEventListener(
                "keydown",
                event => {

                    if (event.key !== "Enter") {
                        return;
                    }


                    event.preventDefault();


                    const input =
                        document.querySelector(
                            "#create-wildcards"
                        );


                    const pattern =
                        input.value.trim();


                    if (!pattern) {
                        return;
                    }


                    const patterns =
                        pattern
                            .split(",")
                            .map(item => item.trim())
                            .filter(
                                item => item !== ""
                            );


                    for (
                        const wildcard
                        of patterns
                    ) {

                        if (
                            !validWildcard(
                                wildcard
                            )
                        ) {

                            showCreateError(
                                `Invalid wildcard: ${wildcard}`
                            );

                            return;

                        }

                    }


                    patterns.forEach(
                        wildcard => {

                            if (
                                !createWildcards.includes(
                                    wildcard
                                )
                            ) {

                                createWildcards.push(
                                    wildcard
                                );

                            }

                        }
                    );


                    input.value = "";

                    clearCreateError();

                }
            );


        document.querySelector(
            "#create-job"
        )
            .addEventListener(
                "click",
                async () => {

                    clearCreateError();


                    const source =
                        document.querySelector(
                            "#create-source"
                        ).value.trim();


                    const destination =
                        document.querySelector(
                            "#create-destination"
                        ).value.trim();


                    const timeValue =
                        document.querySelector(
                            "#create-time"
                        ).value.trim();


                    const timeUnit =
                        document.querySelector(
                            "#create-time-unit"
                        ).value;


                    const zip =
                        document.querySelector(
                            "#create-zip"
                        ).checked;


                    const currentWildcardInput =
                        document.querySelector(
                            "#create-wildcards"
                        ).value.trim();


                    if (currentWildcardInput) {

                        const enteredWildcards =
                            currentWildcardInput
                                .split(",")
                                .map(
                                    item => item.trim()
                                )
                                .filter(
                                    item => item !== ""
                                );


                        for (
                            const wildcard
                            of enteredWildcards
                        ) {

                            if (
                                !validWildcard(
                                    wildcard
                                )
                            ) {

                                showCreateError(
                                    `Invalid wildcard: ${wildcard}`
                                );

                                return;

                            }


                            if (
                                !createWildcards.includes(
                                    wildcard
                                )
                            ) {

                                createWildcards.push(
                                    wildcard
                                );

                            }

                        }

                    }


                    if (!source) {

                        showCreateError(
                            "Please select a source."
                        );

                        return;

                    }


                    if (!destination) {

                        showCreateError(
                            "Please select a destination."
                        );

                        return;

                    }


                    if (!timeValue) {

                        showCreateError(
                            "Please enter a time period."
                        );

                        return;

                    }


                    if (
                        !Number.isInteger(
                            Number(timeValue)
                        ) ||
                        Number(timeValue) <= 0
                    ) {

                        showCreateError(
                            "The time period must be a positive whole number."
                        );

                        return;

                    }


                    const jobData = {

                        source:
                            source,

                        destination:
                            destination,

                        time:
                            timeValue +
                            timeUnit,

                        exceptions:
                            createExceptions,

                        wildcards:
                            createWildcards,

                        zip:
                            zip

                    };


                    const url =
                        editingJobId === null
                            ? "/api/jobs"
                            : `/api/jobs/${editingJobId}`;


                    const method =
                        editingJobId === null
                            ? "POST"
                            : "PUT";


                    try {

                        const response =
                            await fetch(
                                url,
                                {
                                    method:
                                        method,

                                    headers: {
                                        "Content-Type":
                                            "application/json"
                                    },

                                    body:
                                        JSON.stringify(
                                            jobData
                                        )

                                }
                            );


                        const result =
                            await response.json();


                        if (!response.ok) {

                            showCreateError(
                                result.error ||
                                "The inputs are not valid."
                            );

                            return;

                        }


                        if (result.success) {

                            createOverlay.style.display =
                                "none";

                            editingJobId =
                                null;

                            resetCreateForm();

                            location.reload();

                        }

                    }
                    catch (error) {

                        console.error(
                            "Failed to save job:",
                            error
                        );


                        showCreateError(
                            "Could not contact the server."
                        );

                    }

                }
            );

    })
    .catch(error => {

        console.error(
            "Failed to get initial data:",
            error
        );

    });

    function showActionMessage(message) {
    
        const messageBox =
            document.querySelector("#action-message");
    
        messageBox.textContent = message;
        messageBox.style.display = "block";
    
        setTimeout(() => {
            messageBox.style.display = "none";
        }, 2500);
    }