import { useState, useEffect } from 'react';

const useLocalStorage = (key, initialValue) => {
    const [storedValue, setStoredValue] = useState(() => {
        try {
            const item = window.localStorage.getItem(key);
            return item ? JSON.parse(item) : initialValue;
        } catch (error) {
            console.error(error);
            return initialValue;
        }
    });

    const [isSuccess, setIsSuccess] = useState(false);

    useEffect(() => {
        try {
            const item = window.localStorage.getItem(key);
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

        window.addEventListener('storage', handleStorage);
        window.addEventListener('interface-local-storage-updated', handleLocalUpdate);
        return () => {
            window.removeEventListener('storage', handleStorage);
            window.removeEventListener('interface-local-storage-updated', handleLocalUpdate);
        };
    }, [initialValue, key]);

    const setValue = value => {
        try {
            const valueToStore = value instanceof Function ? value(storedValue) : value;
            setStoredValue(valueToStore);
            window.localStorage.setItem(key, JSON.stringify(valueToStore));
            window.dispatchEvent(new CustomEvent('interface-local-storage-updated', {
                detail: { key, value: valueToStore },
            }));
        } catch (error) {
            console.error(error);
        }
    };

    return [storedValue, setValue, isSuccess];
};

export default useLocalStorage;
