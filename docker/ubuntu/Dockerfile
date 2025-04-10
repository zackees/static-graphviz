FROM ubuntu:22.04

# Update
RUN apt-get update

# Install required tools and Graphviz runtime dependencies
RUN apt-get install -y \
    curl \
    xz-utils \
    dpkg \
    file \
    patchelf \
    libpoppler-glib8 \
    librsvg2-2 \
    ghostscript \
    liblasi0 \
    libdevil1c2 \
    libgts-0.7-5 \
    libltdl7 \
    libgd3 \
    libgtk-3-0 \
    libcairo2 && \
    apt-get clean

RUN apt-get install -y \
    libgraphviz-dev \
    libgvc6 \
    libcgraph6 \
    libcdt5 \
    libxdot4 \
    libtiff5 \
    libijs-0.35 \
    libjbig2dec0 \
    libidn12 \
    libpaper1



# Environment variables
ENV GV_URL=https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/12.2.1/ubuntu_22.04_graphviz-12.2.1-debs.tar.xz
ENV GV_FILENAME=ubuntu_22.04_graphviz-12.2.1-debs.tar.xz
ENV OUTPUT_FILENAME=graphviz_libraries_executables-12.2.1.tar.xz

WORKDIR /workspace

# Debug library scan
RUN echo "🔎 Scanning for common system libs..." && \
    for name in libgs libIL libILU libpoppler-glib librsvg-2 libLASi libgts; do \
        echo "🔍 Searching for $name.so* ..."; \
        find / -type f -name "$name.so*" 2>/dev/null || echo "⚠️  Not found: $name.so*"; \
    done

# Download and extract Graphviz DEBs
RUN curl -L "$GV_URL" -o "$GV_FILENAME"
RUN mkdir -p debs extracted bins
RUN tar -xf "$GV_FILENAME" -C debs
RUN for deb in debs/*.deb; do dpkg-deb -x "$deb" extracted/; done

# Plugin validation
RUN echo "🔍 Checking for libgvplugin_lasi.so.6.0.0..." && \
    (find extracted -name 'libgvplugin_lasi.so.6.0.0' -exec echo "✅ Found: {}" \; || echo "❌ Not found")

# Copy binaries and libraries
RUN [ -d extracted/usr/bin ] && cp -a extracted/usr/bin/* bins/ || true
RUN [ -d extracted/usr/lib ] && cp -a extracted/usr/lib/* bins/ || true

# Copy specific plugin dependencies
RUN cp --parents -d $(find extracted/usr/lib -name 'libxdot.so*') bins/ || true

# Copy libxdot.so.4* from system library paths
RUN echo "📎 Copying system libxdot.so.4* into bins/..." && \
    find /usr/lib /lib -name 'libxdot.so.4*' -exec cp --parents -d {} /workspace/bins/ \;


RUN cp --parents -d $(find extracted/usr/lib -name 'libpathplan.so*') bins/ || true
RUN cp --parents -d $(find extracted/usr/lib -name 'libcdt.so*') bins/ || true
RUN for dir in extracted/usr/lib extracted/usr/lib/x86_64-linux-gnu extracted/usr/lib/graphviz; do \
        [ -d "$dir" ] && find "$dir" \( -type f -o -type l \) -name '*.so*' -exec cp --parents -d {} bins/ \;; \
    done

# Print what we collected
RUN echo "📋 Copied shared libraries:" && find bins -name '*.so*'
RUN echo "✅ Expecting libgvc, libcgraph, etc. to now appear:" && \
    find bins -name 'libgvc*.so*' && find bins -name 'libcgraph*.so*'


# Copy libgvc/libcgraph early to ensure ldd doesn't fail
RUN echo "📦 Ensuring libgvc and libcgraph are copied early..." && \
    find extracted -type f \( -name 'libgvc.so*' -o -name 'libcgraph.so*' \) -exec cp --parents -d {} bins/ \;

# Copy core libs into every plugin dir to ensure $ORIGIN RPATH works
RUN echo "📎 Copying libgvc/libcgraph into plugin dirs..." && \
    find bins -name 'libgvplugin_*.so*' -exec dirname {} \; | sort -u | while read dir; do \
        cp bins/libgvc.so.* "$dir/" || true; \
        cp bins/libcgraph.so.* "$dir/" || true; \
    done

# Auto-copy specific shared libraries needed by libgvplugin_gs.so.6.0.0
RUN echo "📎 Copying missing dependencies for libgvplugin_gs.so.6.0.0..." && \
    for lib in libtiff.so.5 libijs-0.35.so libjbig2dec.so.0 libidn.so.12 libpaper.so.1; do \
        path=$(ldconfig -p | grep "$lib" | awk '{print $NF}' | head -n1); \
        if [ -f "$path" ]; then \
            echo "📎 Copying $lib from $path"; \
            cp --parents -d "$path" /workspace/bins/; \
        else \
            echo "⚠️  $lib not found in ldconfig output"; \
        fi; \
    done

# 🚫 Strip unsafe system libs
RUN find bins/graphviz -name 'libc.so.*' -delete && \
    find bins/graphviz -name 'libpthread.so.*' -delete && \
    find bins/graphviz -name 'ld-linux*.so.*' -delete && \
    find bins/graphviz -name 'libm.so.*' -delete && \
    find bins/graphviz -name 'libdl.so.*' -delete && \
    find bins/graphviz -name 'librt.so.*' -delete


RUN echo "📎 Copying verified resolved GS plugin dependencies..." && \
    for lib in libtiff.so.5 libijs-0.35.so libjbig2dec.so.0 libidn.so.12 libpaper.so.1; do \
        find /lib /usr/lib /usr/lib/x86_64-linux-gnu -name "$lib" -exec cp --parents -d {} /workspace/bins/ \; || echo "⚠️ $lib not found"; \
    done

# Patch RPATHs after plugin placement
RUN echo "🔧 Patching RPATH for executable ELF files..." && \
    find bins -type f -exec file {} \; | grep "ELF.*executable" | cut -d: -f1 | while read exe; do \
        echo "🔧 Setting RPATH for $exe"; \
        patchelf --set-rpath '$ORIGIN' "$exe"; \
    done

RUN echo "🔧 Patching RPATH for plugin .so files..." && \
    find bins -type f -name 'libgvplugin_*.so*' -exec patchelf --set-rpath '$ORIGIN' {} \;

# Resolve plugin dependencies with ldd
RUN echo "🔗 Resolving plugin dependencies with ldd..." && \
    find bins -type f -name 'libgvplugin_*.so*' | while read plugin; do \
        echo "🧩 ldd $plugin:"; \
        ldd "$plugin" | awk '{ print $1, $2, $3 }' | while read name arrow path; do \
            if [ "$arrow" = "=>" ] && [ "$path" != "not" ]; then \
                echo "📎 Copying $name => $path"; \
                cp --parents -d "$path" bins/ || { echo "❌ Failed to copy $path"; exit 1; }; \
            elif [ "$arrow" = "=>" ] && [ "$path" = "not" ]; then \
                echo "❌ Missing dependency: $name"; exit 1; \
            fi; \
        done; \
    done

# 🩹 Manually ensure GS plugin dependencies go to bins/
RUN echo "📎 Forcing GS plugin dependencies into bins/..." && \
    for lib in libtiff.so.5 libijs-0.35.so libjbig2dec.so.0 libidn.so.12 libpaper.so.1; do \
        path=$(ldconfig -p | grep "$lib" | awk '{print $NF}' | head -n1); \
        if [ -f "$path" ]; then \
            echo "📎 Copying $lib from $path -> bins/"; \
            cp -d "$path" bins/ || echo "⚠️  Failed to copy $lib"; \
        else \
            echo "⚠️  $lib not found in ldconfig output"; \
        fi; \
    done


# ✅ Finda nd copy runtime dependencies missed by ldd
RUN echo "📎 Recursively resolving all shared library dependencies..." && \
    set -e && \
    mkdir -p bins/graphviz && \
    find bins -type f -executable -o -name '*.so*' | while read -r sofile; do \
        echo "🔍 Scanning $sofile"; \
        ldd "$sofile" | awk '/=>/ && $3 ~ /^\// { print $3 }' \
            | sort -u >> /tmp/all-libs.txt || true; \
    done && \
    sort -u /tmp/all-libs.txt > /tmp/all-libs.sorted.txt && \
    echo "📦 Copying discovered libs..." && \
    while read -r libpath; do \
        [ -f "$libpath" ] || continue; \
        echo "📎 Copying $libpath"; \
        mkdir -p "$(dirname "bins/$libpath")"; \
        cp -d "$libpath" "bins/$libpath" || true; \
        cp "$libpath" bins/graphviz/ || true; \
    done < /tmp/all-libs.sorted.txt && \
    echo "✅ All transitive shared libs copied"


RUN echo "🔧 Re-patching RPATH for all .so files to use \$ORIGIN..." && \
    find bins -type f -name '*.so*' -exec patchelf --set-rpath '$ORIGIN' {} \;

# Create archive
RUN echo "📦 Creating final archive..." && \
    tar -cJf "$OUTPUT_FILENAME" -C bins .

# Verify contents
RUN echo "🧾 Verifying archive contents..." && \
    tar -tvf "$OUTPUT_FILENAME" | grep -E 'libgvplugin_.*\.so|libpoppler|librsvg|libgs|libIL|libLASi|libgvc|libcgraph' || echo "⚠️ Some items may still be missing"

# Final test: extract and test RPATH loading
RUN echo "🧪 Post-archive testing..." && \
    mkdir test_extract && \
    tar -xf "$OUTPUT_FILENAME" -C test_extract && \
    echo "🔍 ldd on test_extract/dot:" && ldd test_extract/dot || echo "❌ dot ldd failed" && \
    echo "🔍 ldd on libgvplugin_gs.so.6.0.0:" && \
    LD_LIBRARY_PATH=test_extract/graphviz:test_extract ldd test_extract/graphviz/libgvplugin_gs.so.6.0.0 || echo "⚠️ Linking failed"

# Final confirmation
RUN echo "✅ Final lib check:" && \
    find bins -name 'libgvc*.so*' && find bins -name 'libcgraph*.so*'

# Optionally copy result to a mounted volume
CMD ["/bin/bash", "-c", "if [ -d /host ] && [ -w /host ]; then cp \"/workspace/$OUTPUT_FILENAME\" /host/ && echo '✅ Archive copied to /host/'; else echo '⚠️ No writable /host mount detected. Skipping copy.'; fi"]
