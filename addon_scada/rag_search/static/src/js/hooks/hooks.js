/** @odoo-module **/

import {onMounted, reactive, useEffect} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";

export function useAutoFocus(ref) {
    onMounted(() => {
        if (ref.el) {
            ref.el.focus();
        }
    });
}

export function useAutoScrollBottom(ref, deps = []) {
    useEffect(
        () => {
            if (ref.el) {
                ref.el.scrollTop = ref.el.scrollHeight;
            }
        },
        () => deps
    );
}

export function useAutoResizeTextarea(ref) {
    return () => {
        if (ref.el) {
            ref.el.style.height = "auto";
            ref.el.style.height = `${ref.el.scrollHeight}px`;
        }
    };
}

export async function useStreamReader(url, onData) {
    const response = await fetch(url);
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let result = '';
    while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        result += chunk;
        onData(chunk);
    }

    return result;
}

export function useLLM(main_url) {
    const rpc = useService("rpc");

    const state = reactive({
        isLoading: false,
        error: null,
    });

    async function get(prompt, session_id = null) {
        state.isLoading = true;
        state.error = null;
        try {
            return await rpc(main_url, {
                prompt,
                session_id,
            });
        } catch (e) {
            state.error = e.message || "LLM error";
            return null;
        } finally {
            state.isLoading = false;
        }
    }

    async function getSearch(prompt, threshold = null, summarized= false) {
        state.isLoading = true;
        state.error = null;
        try {
            return await rpc(main_url, {
                query: prompt,
                top_k: 10,
                threshold: threshold || 0.80,
                summarized,
            });
        } catch (e) {
            state.error = e.message || "LLM error";
            return null;
        } finally {
            state.isLoading = false;
        }
    }

    async function stream({prompt, session_id = null, onChunk}) {
        state.isLoading = true;
        state.error = null;

        try {
            const url = `${main_url}/stream/?text=${encodeURIComponent(prompt)}${session_id ? `&session_id=${session_id}` : ''}`;
            const response = await fetch(url);
            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');

            let fullText = '';
            while (true) {
                const {done, value} = await reader.read();
                if (done) break;
                const chunk = decoder.decode(value);
                fullText += chunk;
                onChunk?.(chunk);
            }

            return fullText;
        } catch (e) {
            state.error = e.message || "Streaming error";
            return null;
        } finally {
            state.isLoading = false;
        }
    }

    async function search(prompt, threshold = null, summarized= false, is_stream = false, onChunk) {
        if (!is_stream) {
            return getSearch(prompt, threshold, summarized);
        }
        const response = await getSearch(prompt, threshold, summarized);
        await stream({
            prompt,
            session_id: null,
            onChunk: (chunk) => {
                if (onChunk) {
                    onChunk(chunk);
                }
            }
        })
        return response;
    }

    return {get, stream, search, getSearch, state};
}