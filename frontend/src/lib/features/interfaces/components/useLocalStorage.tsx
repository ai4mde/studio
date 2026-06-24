import { useState, useEffect } from 'react';

const useLocalStorage = (key, initialValue) => {
    const [storedValue, setStoredValue] = useState(() => {
        try {
            const item = globalThis.localStorage.getItem(key);
            return item ? JSON.parse(item) : initialValue;
        } catch (error) {
            console.error(error);
            return initialValue;
        }
    });

    const [isSuccess, setIsSuccess] = useState(false);

    useEffect(() => {
        try {
            const item = globalThis.localStorage.getItem(key);
            setStoredValue(item ? JSON.parse(item) : initialValue);
        } catch (error) {
            console.error(error);
            setStoredValue(initialValue);
        }
    }, [key]);

    useEffect(() => {
        if (storedValue !== initialValue) {
            setIsSuccess(true);
        }
    }, [storedValue, initialValue]);

    useEffect(() => {
        const handleStorage = (event) => {
            if (event.key !== key) return;
            try {
                setStoredValue(event.newValue ? JSON.parse(event.newValue) : initialValue);
            } catch (error) {
                console.error(error);
            }
        };

        const handleLocalUpdate = (event) => {
            if (event.detail?.key !== key) return;
            setStoredValue(event.detail.value);
        };

        globalThis.addEventListener('storage', handleStorage);
        globalThis.addEventListener('interface-local-storage-updated', handleLocalUpdate);
        return () => {
            globalThis.removeEventListener('storage', handleStorage);
            globalThis.removeEventListener('interface-local-storage-updated', handleLocalUpdate);
        };
    }, [initialValue, key]);

    const setValue = value => {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);

        try {
            globalThis.localStorage.setItem(key, JSON.stringify(valueToStore));
        } catch (error) {
            console.error(error);
        }

        globalThis.dispatchEvent(new CustomEvent('interface-local-storage-updated', {
            detail: { key, value: valueToStore },
        }));
    };

    return [storedValue, setValue, isSuccess];
};

export default useLocalStorage;
