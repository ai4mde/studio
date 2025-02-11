import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle
} from "/build/_shared/chunk-ANELKYHI.js";
import {
  Button
} from "/build/_shared/chunk-MI2YJZX6.js";
import "/build/_shared/chunk-2WFCNDEW.js";
import {
  MaxWidthWrapper
} from "/build/_shared/chunk-X6FLJXIJ.js";
import {
  Link
} from "/build/_shared/chunk-5SMQHKI5.js";
import {
  cn
} from "/build/_shared/chunk-3DKJGO2R.js";
import "/build/_shared/chunk-2N23GYW7.js";
import {
  require_jsx_dev_runtime
} from "/build/_shared/chunk-G5LS6WKY.js";
import {
  require_react
} from "/build/_shared/chunk-QPVUD6NO.js";
import {
  createHotContext
} from "/build/_shared/chunk-YJEMTN56.js";
import "/build/_shared/chunk-MWML3QXM.js";
import {
  __toESM
} from "/build/_shared/chunk-PZDJHGND.js";

// app/components/ui/carousel.tsx
var React = __toESM(require_react(), 1);

// node_modules/.pnpm/embla-carousel-react@8.5.2_react@18.3.1/node_modules/embla-carousel-react/esm/embla-carousel-react.esm.js
var import_react = __toESM(require_react(), 1);

// node_modules/.pnpm/embla-carousel-reactive-utils@8.5.2_embla-carousel@8.5.2/node_modules/embla-carousel-reactive-utils/esm/embla-carousel-reactive-utils.esm.js
function isObject(subject) {
  return Object.prototype.toString.call(subject) === "[object Object]";
}
function isRecord(subject) {
  return isObject(subject) || Array.isArray(subject);
}
function canUseDOM() {
  return !!(typeof window !== "undefined" && window.document && window.document.createElement);
}
function areOptionsEqual(optionsA, optionsB) {
  const optionsAKeys = Object.keys(optionsA);
  const optionsBKeys = Object.keys(optionsB);
  if (optionsAKeys.length !== optionsBKeys.length)
    return false;
  const breakpointsA = JSON.stringify(Object.keys(optionsA.breakpoints || {}));
  const breakpointsB = JSON.stringify(Object.keys(optionsB.breakpoints || {}));
  if (breakpointsA !== breakpointsB)
    return false;
  return optionsAKeys.every((key) => {
    const valueA = optionsA[key];
    const valueB = optionsB[key];
    if (typeof valueA === "function")
      return `${valueA}` === `${valueB}`;
    if (!isRecord(valueA) || !isRecord(valueB))
      return valueA === valueB;
    return areOptionsEqual(valueA, valueB);
  });
}
function sortAndMapPluginToOptions(plugins) {
  return plugins.concat().sort((a2, b2) => a2.name > b2.name ? 1 : -1).map((plugin) => plugin.options);
}
function arePluginsEqual(pluginsA, pluginsB) {
  if (pluginsA.length !== pluginsB.length)
    return false;
  const optionsA = sortAndMapPluginToOptions(pluginsA);
  const optionsB = sortAndMapPluginToOptions(pluginsB);
  return optionsA.every((optionA, index) => {
    const optionB = optionsB[index];
    return areOptionsEqual(optionA, optionB);
  });
}

// node_modules/.pnpm/embla-carousel@8.5.2/node_modules/embla-carousel/esm/embla-carousel.esm.js
function isNumber(subject) {
  return typeof subject === "number";
}
function isString(subject) {
  return typeof subject === "string";
}
function isBoolean(subject) {
  return typeof subject === "boolean";
}
function isObject2(subject) {
  return Object.prototype.toString.call(subject) === "[object Object]";
}
function mathAbs(n2) {
  return Math.abs(n2);
}
function mathSign(n2) {
  return Math.sign(n2);
}
function deltaAbs(valueB, valueA) {
  return mathAbs(valueB - valueA);
}
function factorAbs(valueB, valueA) {
  if (valueB === 0 || valueA === 0)
    return 0;
  if (mathAbs(valueB) <= mathAbs(valueA))
    return 0;
  const diff = deltaAbs(mathAbs(valueB), mathAbs(valueA));
  return mathAbs(diff / valueB);
}
function roundToTwoDecimals(num) {
  return Math.round(num * 100) / 100;
}
function arrayKeys(array) {
  return objectKeys(array).map(Number);
}
function arrayLast(array) {
  return array[arrayLastIndex(array)];
}
function arrayLastIndex(array) {
  return Math.max(0, array.length - 1);
}
function arrayIsLastIndex(array, index) {
  return index === arrayLastIndex(array);
}
function arrayFromNumber(n2, startAt = 0) {
  return Array.from(Array(n2), (_, i2) => startAt + i2);
}
function objectKeys(object) {
  return Object.keys(object);
}
function objectsMergeDeep(objectA, objectB) {
  return [objectA, objectB].reduce((mergedObjects, currentObject) => {
    objectKeys(currentObject).forEach((key) => {
      const valueA = mergedObjects[key];
      const valueB = currentObject[key];
      const areObjects = isObject2(valueA) && isObject2(valueB);
      mergedObjects[key] = areObjects ? objectsMergeDeep(valueA, valueB) : valueB;
    });
    return mergedObjects;
  }, {});
}
function isMouseEvent(evt, ownerWindow) {
  return typeof ownerWindow.MouseEvent !== "undefined" && evt instanceof ownerWindow.MouseEvent;
}
function Alignment(align, viewSize) {
  const predefined = {
    start,
    center,
    end
  };
  function start() {
    return 0;
  }
  function center(n2) {
    return end(n2) / 2;
  }
  function end(n2) {
    return viewSize - n2;
  }
  function measure(n2, index) {
    if (isString(align))
      return predefined[align](n2);
    return align(viewSize, n2, index);
  }
  const self = {
    measure
  };
  return self;
}
function EventStore() {
  let listeners = [];
  function add(node, type, handler, options = {
    passive: true
  }) {
    let removeListener;
    if ("addEventListener" in node) {
      node.addEventListener(type, handler, options);
      removeListener = () => node.removeEventListener(type, handler, options);
    } else {
      const legacyMediaQueryList = node;
      legacyMediaQueryList.addListener(handler);
      removeListener = () => legacyMediaQueryList.removeListener(handler);
    }
    listeners.push(removeListener);
    return self;
  }
  function clear() {
    listeners = listeners.filter((remove) => remove());
  }
  const self = {
    add,
    clear
  };
  return self;
}
function Animations(ownerDocument, ownerWindow, update, render) {
  const documentVisibleHandler = EventStore();
  const fixedTimeStep = 1e3 / 60;
  let lastTimeStamp = null;
  let accumulatedTime = 0;
  let animationId = 0;
  function init() {
    documentVisibleHandler.add(ownerDocument, "visibilitychange", () => {
      if (ownerDocument.hidden)
        reset();
    });
  }
  function destroy() {
    stop();
    documentVisibleHandler.clear();
  }
  function animate(timeStamp) {
    if (!animationId)
      return;
    if (!lastTimeStamp) {
      lastTimeStamp = timeStamp;
      update();
      update();
    }
    const timeElapsed = timeStamp - lastTimeStamp;
    lastTimeStamp = timeStamp;
    accumulatedTime += timeElapsed;
    while (accumulatedTime >= fixedTimeStep) {
      update();
      accumulatedTime -= fixedTimeStep;
    }
    const alpha = accumulatedTime / fixedTimeStep;
    render(alpha);
    if (animationId) {
      animationId = ownerWindow.requestAnimationFrame(animate);
    }
  }
  function start() {
    if (animationId)
      return;
    animationId = ownerWindow.requestAnimationFrame(animate);
  }
  function stop() {
    ownerWindow.cancelAnimationFrame(animationId);
    lastTimeStamp = null;
    accumulatedTime = 0;
    animationId = 0;
  }
  function reset() {
    lastTimeStamp = null;
    accumulatedTime = 0;
  }
  const self = {
    init,
    destroy,
    start,
    stop,
    update,
    render
  };
  return self;
}
function Axis(axis, contentDirection) {
  const isRightToLeft = contentDirection === "rtl";
  const isVertical = axis === "y";
  const scroll = isVertical ? "y" : "x";
  const cross = isVertical ? "x" : "y";
  const sign = !isVertical && isRightToLeft ? -1 : 1;
  const startEdge = getStartEdge();
  const endEdge = getEndEdge();
  function measureSize(nodeRect) {
    const {
      height,
      width
    } = nodeRect;
    return isVertical ? height : width;
  }
  function getStartEdge() {
    if (isVertical)
      return "top";
    return isRightToLeft ? "right" : "left";
  }
  function getEndEdge() {
    if (isVertical)
      return "bottom";
    return isRightToLeft ? "left" : "right";
  }
  function direction(n2) {
    return n2 * sign;
  }
  const self = {
    scroll,
    cross,
    startEdge,
    endEdge,
    measureSize,
    direction
  };
  return self;
}
function Limit(min = 0, max = 0) {
  const length = mathAbs(min - max);
  function reachedMin(n2) {
    return n2 < min;
  }
  function reachedMax(n2) {
    return n2 > max;
  }
  function reachedAny(n2) {
    return reachedMin(n2) || reachedMax(n2);
  }
  function constrain(n2) {
    if (!reachedAny(n2))
      return n2;
    return reachedMin(n2) ? min : max;
  }
  function removeOffset(n2) {
    if (!length)
      return n2;
    return n2 - length * Math.ceil((n2 - max) / length);
  }
  const self = {
    length,
    max,
    min,
    constrain,
    reachedAny,
    reachedMax,
    reachedMin,
    removeOffset
  };
  return self;
}
function Counter(max, start, loop) {
  const {
    constrain
  } = Limit(0, max);
  const loopEnd = max + 1;
  let counter = withinLimit(start);
  function withinLimit(n2) {
    return !loop ? constrain(n2) : mathAbs((loopEnd + n2) % loopEnd);
  }
  function get() {
    return counter;
  }
  function set(n2) {
    counter = withinLimit(n2);
    return self;
  }
  function add(n2) {
    return clone().set(get() + n2);
  }
  function clone() {
    return Counter(max, get(), loop);
  }
  const self = {
    get,
    set,
    add,
    clone
  };
  return self;
}
function DragHandler(axis, rootNode, ownerDocument, ownerWindow, target, dragTracker, location, animation, scrollTo, scrollBody, scrollTarget, index, eventHandler, percentOfView, dragFree, dragThreshold, skipSnaps, baseFriction, watchDrag) {
  const {
    cross: crossAxis,
    direction
  } = axis;
  const focusNodes = ["INPUT", "SELECT", "TEXTAREA"];
  const nonPassiveEvent = {
    passive: false
  };
  const initEvents = EventStore();
  const dragEvents = EventStore();
  const goToNextThreshold = Limit(50, 225).constrain(percentOfView.measure(20));
  const snapForceBoost = {
    mouse: 300,
    touch: 400
  };
  const freeForceBoost = {
    mouse: 500,
    touch: 600
  };
  const baseSpeed = dragFree ? 43 : 25;
  let isMoving = false;
  let startScroll = 0;
  let startCross = 0;
  let pointerIsDown = false;
  let preventScroll = false;
  let preventClick = false;
  let isMouse = false;
  function init(emblaApi) {
    if (!watchDrag)
      return;
    function downIfAllowed(evt) {
      if (isBoolean(watchDrag) || watchDrag(emblaApi, evt))
        down(evt);
    }
    const node = rootNode;
    initEvents.add(node, "dragstart", (evt) => evt.preventDefault(), nonPassiveEvent).add(node, "touchmove", () => void 0, nonPassiveEvent).add(node, "touchend", () => void 0).add(node, "touchstart", downIfAllowed).add(node, "mousedown", downIfAllowed).add(node, "touchcancel", up).add(node, "contextmenu", up).add(node, "click", click, true);
  }
  function destroy() {
    initEvents.clear();
    dragEvents.clear();
  }
  function addDragEvents() {
    const node = isMouse ? ownerDocument : rootNode;
    dragEvents.add(node, "touchmove", move, nonPassiveEvent).add(node, "touchend", up).add(node, "mousemove", move, nonPassiveEvent).add(node, "mouseup", up);
  }
  function isFocusNode(node) {
    const nodeName = node.nodeName || "";
    return focusNodes.includes(nodeName);
  }
  function forceBoost() {
    const boost = dragFree ? freeForceBoost : snapForceBoost;
    const type = isMouse ? "mouse" : "touch";
    return boost[type];
  }
  function allowedForce(force, targetChanged) {
    const next = index.add(mathSign(force) * -1);
    const baseForce = scrollTarget.byDistance(force, !dragFree).distance;
    if (dragFree || mathAbs(force) < goToNextThreshold)
      return baseForce;
    if (skipSnaps && targetChanged)
      return baseForce * 0.5;
    return scrollTarget.byIndex(next.get(), 0).distance;
  }
  function down(evt) {
    const isMouseEvt = isMouseEvent(evt, ownerWindow);
    isMouse = isMouseEvt;
    preventClick = dragFree && isMouseEvt && !evt.buttons && isMoving;
    isMoving = deltaAbs(target.get(), location.get()) >= 2;
    if (isMouseEvt && evt.button !== 0)
      return;
    if (isFocusNode(evt.target))
      return;
    pointerIsDown = true;
    dragTracker.pointerDown(evt);
    scrollBody.useFriction(0).useDuration(0);
    target.set(location);
    addDragEvents();
    startScroll = dragTracker.readPoint(evt);
    startCross = dragTracker.readPoint(evt, crossAxis);
    eventHandler.emit("pointerDown");
  }
  function move(evt) {
    const isTouchEvt = !isMouseEvent(evt, ownerWindow);
    if (isTouchEvt && evt.touches.length >= 2)
      return up(evt);
    const lastScroll = dragTracker.readPoint(evt);
    const lastCross = dragTracker.readPoint(evt, crossAxis);
    const diffScroll = deltaAbs(lastScroll, startScroll);
    const diffCross = deltaAbs(lastCross, startCross);
    if (!preventScroll && !isMouse) {
      if (!evt.cancelable)
        return up(evt);
      preventScroll = diffScroll > diffCross;
      if (!preventScroll)
        return up(evt);
    }
    const diff = dragTracker.pointerMove(evt);
    if (diffScroll > dragThreshold)
      preventClick = true;
    scrollBody.useFriction(0.3).useDuration(0.75);
    animation.start();
    target.add(direction(diff));
    evt.preventDefault();
  }
  function up(evt) {
    const currentLocation = scrollTarget.byDistance(0, false);
    const targetChanged = currentLocation.index !== index.get();
    const rawForce = dragTracker.pointerUp(evt) * forceBoost();
    const force = allowedForce(direction(rawForce), targetChanged);
    const forceFactor = factorAbs(rawForce, force);
    const speed = baseSpeed - 10 * forceFactor;
    const friction = baseFriction + forceFactor / 50;
    preventScroll = false;
    pointerIsDown = false;
    dragEvents.clear();
    scrollBody.useDuration(speed).useFriction(friction);
    scrollTo.distance(force, !dragFree);
    isMouse = false;
    eventHandler.emit("pointerUp");
  }
  function click(evt) {
    if (preventClick) {
      evt.stopPropagation();
      evt.preventDefault();
      preventClick = false;
    }
  }
  function pointerDown() {
    return pointerIsDown;
  }
  const self = {
    init,
    destroy,
    pointerDown
  };
  return self;
}
function DragTracker(axis, ownerWindow) {
  const logInterval = 170;
  let startEvent;
  let lastEvent;
  function readTime(evt) {
    return evt.timeStamp;
  }
  function readPoint(evt, evtAxis) {
    const property = evtAxis || axis.scroll;
    const coord = `client${property === "x" ? "X" : "Y"}`;
    return (isMouseEvent(evt, ownerWindow) ? evt : evt.touches[0])[coord];
  }
  function pointerDown(evt) {
    startEvent = evt;
    lastEvent = evt;
    return readPoint(evt);
  }
  function pointerMove(evt) {
    const diff = readPoint(evt) - readPoint(lastEvent);
    const expired = readTime(evt) - readTime(startEvent) > logInterval;
    lastEvent = evt;
    if (expired)
      startEvent = evt;
    return diff;
  }
  function pointerUp(evt) {
    if (!startEvent || !lastEvent)
      return 0;
    const diffDrag = readPoint(lastEvent) - readPoint(startEvent);
    const diffTime = readTime(evt) - readTime(startEvent);
    const expired = readTime(evt) - readTime(lastEvent) > logInterval;
    const force = diffDrag / diffTime;
    const isFlick = diffTime && !expired && mathAbs(force) > 0.1;
    return isFlick ? force : 0;
  }
  const self = {
    pointerDown,
    pointerMove,
    pointerUp,
    readPoint
  };
  return self;
}
function NodeRects() {
  function measure(node) {
    const {
      offsetTop,
      offsetLeft,
      offsetWidth,
      offsetHeight
    } = node;
    const offset = {
      top: offsetTop,
      right: offsetLeft + offsetWidth,
      bottom: offsetTop + offsetHeight,
      left: offsetLeft,
      width: offsetWidth,
      height: offsetHeight
    };
    return offset;
  }
  const self = {
    measure
  };
  return self;
}
function PercentOfView(viewSize) {
  function measure(n2) {
    return viewSize * (n2 / 100);
  }
  const self = {
    measure
  };
  return self;
}
function ResizeHandler(container, eventHandler, ownerWindow, slides, axis, watchResize, nodeRects) {
  const observeNodes = [container].concat(slides);
  let resizeObserver;
  let containerSize;
  let slideSizes = [];
  let destroyed = false;
  function readSize(node) {
    return axis.measureSize(nodeRects.measure(node));
  }
  function init(emblaApi) {
    if (!watchResize)
      return;
    containerSize = readSize(container);
    slideSizes = slides.map(readSize);
    function defaultCallback(entries) {
      for (const entry of entries) {
        if (destroyed)
          return;
        const isContainer = entry.target === container;
        const slideIndex = slides.indexOf(entry.target);
        const lastSize = isContainer ? containerSize : slideSizes[slideIndex];
        const newSize = readSize(isContainer ? container : slides[slideIndex]);
        const diffSize = mathAbs(newSize - lastSize);
        if (diffSize >= 0.5) {
          emblaApi.reInit();
          eventHandler.emit("resize");
          break;
        }
      }
    }
    resizeObserver = new ResizeObserver((entries) => {
      if (isBoolean(watchResize) || watchResize(emblaApi, entries)) {
        defaultCallback(entries);
      }
    });
    ownerWindow.requestAnimationFrame(() => {
      observeNodes.forEach((node) => resizeObserver.observe(node));
    });
  }
  function destroy() {
    destroyed = true;
    if (resizeObserver)
      resizeObserver.disconnect();
  }
  const self = {
    init,
    destroy
  };
  return self;
}
function ScrollBody(location, offsetLocation, previousLocation, target, baseDuration, baseFriction) {
  let scrollVelocity = 0;
  let scrollDirection = 0;
  let scrollDuration = baseDuration;
  let scrollFriction = baseFriction;
  let rawLocation = location.get();
  let rawLocationPrevious = 0;
  function seek() {
    const displacement = target.get() - location.get();
    const isInstant = !scrollDuration;
    let scrollDistance = 0;
    if (isInstant) {
      scrollVelocity = 0;
      previousLocation.set(target);
      location.set(target);
      scrollDistance = displacement;
    } else {
      previousLocation.set(location);
      scrollVelocity += displacement / scrollDuration;
      scrollVelocity *= scrollFriction;
      rawLocation += scrollVelocity;
      location.add(scrollVelocity);
      scrollDistance = rawLocation - rawLocationPrevious;
    }
    scrollDirection = mathSign(scrollDistance);
    rawLocationPrevious = rawLocation;
    return self;
  }
  function settled() {
    const diff = target.get() - offsetLocation.get();
    return mathAbs(diff) < 1e-3;
  }
  function duration() {
    return scrollDuration;
  }
  function direction() {
    return scrollDirection;
  }
  function velocity() {
    return scrollVelocity;
  }
  function useBaseDuration() {
    return useDuration(baseDuration);
  }
  function useBaseFriction() {
    return useFriction(baseFriction);
  }
  function useDuration(n2) {
    scrollDuration = n2;
    return self;
  }
  function useFriction(n2) {
    scrollFriction = n2;
    return self;
  }
  const self = {
    direction,
    duration,
    velocity,
    seek,
    settled,
    useBaseFriction,
    useBaseDuration,
    useFriction,
    useDuration
  };
  return self;
}
function ScrollBounds(limit, location, target, scrollBody, percentOfView) {
  const pullBackThreshold = percentOfView.measure(10);
  const edgeOffsetTolerance = percentOfView.measure(50);
  const frictionLimit = Limit(0.1, 0.99);
  let disabled = false;
  function shouldConstrain() {
    if (disabled)
      return false;
    if (!limit.reachedAny(target.get()))
      return false;
    if (!limit.reachedAny(location.get()))
      return false;
    return true;
  }
  function constrain(pointerDown) {
    if (!shouldConstrain())
      return;
    const edge = limit.reachedMin(location.get()) ? "min" : "max";
    const diffToEdge = mathAbs(limit[edge] - location.get());
    const diffToTarget = target.get() - location.get();
    const friction = frictionLimit.constrain(diffToEdge / edgeOffsetTolerance);
    target.subtract(diffToTarget * friction);
    if (!pointerDown && mathAbs(diffToTarget) < pullBackThreshold) {
      target.set(limit.constrain(target.get()));
      scrollBody.useDuration(25).useBaseFriction();
    }
  }
  function toggleActive(active) {
    disabled = !active;
  }
  const self = {
    shouldConstrain,
    constrain,
    toggleActive
  };
  return self;
}
function ScrollContain(viewSize, contentSize, snapsAligned, containScroll, pixelTolerance) {
  const scrollBounds = Limit(-contentSize + viewSize, 0);
  const snapsBounded = measureBounded();
  const scrollContainLimit = findScrollContainLimit();
  const snapsContained = measureContained();
  function usePixelTolerance(bound, snap) {
    return deltaAbs(bound, snap) <= 1;
  }
  function findScrollContainLimit() {
    const startSnap = snapsBounded[0];
    const endSnap = arrayLast(snapsBounded);
    const min = snapsBounded.lastIndexOf(startSnap);
    const max = snapsBounded.indexOf(endSnap) + 1;
    return Limit(min, max);
  }
  function measureBounded() {
    return snapsAligned.map((snapAligned, index) => {
      const {
        min,
        max
      } = scrollBounds;
      const snap = scrollBounds.constrain(snapAligned);
      const isFirst = !index;
      const isLast = arrayIsLastIndex(snapsAligned, index);
      if (isFirst)
        return max;
      if (isLast)
        return min;
      if (usePixelTolerance(min, snap))
        return min;
      if (usePixelTolerance(max, snap))
        return max;
      return snap;
    }).map((scrollBound) => parseFloat(scrollBound.toFixed(3)));
  }
  function measureContained() {
    if (contentSize <= viewSize + pixelTolerance)
      return [scrollBounds.max];
    if (containScroll === "keepSnaps")
      return snapsBounded;
    const {
      min,
      max
    } = scrollContainLimit;
    return snapsBounded.slice(min, max);
  }
  const self = {
    snapsContained,
    scrollContainLimit
  };
  return self;
}
function ScrollLimit(contentSize, scrollSnaps, loop) {
  const max = scrollSnaps[0];
  const min = loop ? max - contentSize : arrayLast(scrollSnaps);
  const limit = Limit(min, max);
  const self = {
    limit
  };
  return self;
}
function ScrollLooper(contentSize, limit, location, vectors) {
  const jointSafety = 0.1;
  const min = limit.min + jointSafety;
  const max = limit.max + jointSafety;
  const {
    reachedMin,
    reachedMax
  } = Limit(min, max);
  function shouldLoop(direction) {
    if (direction === 1)
      return reachedMax(location.get());
    if (direction === -1)
      return reachedMin(location.get());
    return false;
  }
  function loop(direction) {
    if (!shouldLoop(direction))
      return;
    const loopDistance = contentSize * (direction * -1);
    vectors.forEach((v2) => v2.add(loopDistance));
  }
  const self = {
    loop
  };
  return self;
}
function ScrollProgress(limit) {
  const {
    max,
    length
  } = limit;
  function get(n2) {
    const currentLocation = n2 - max;
    return length ? currentLocation / -length : 0;
  }
  const self = {
    get
  };
  return self;
}
function ScrollSnaps(axis, alignment, containerRect, slideRects, slidesToScroll) {
  const {
    startEdge,
    endEdge
  } = axis;
  const {
    groupSlides
  } = slidesToScroll;
  const alignments = measureSizes().map(alignment.measure);
  const snaps = measureUnaligned();
  const snapsAligned = measureAligned();
  function measureSizes() {
    return groupSlides(slideRects).map((rects) => arrayLast(rects)[endEdge] - rects[0][startEdge]).map(mathAbs);
  }
  function measureUnaligned() {
    return slideRects.map((rect) => containerRect[startEdge] - rect[startEdge]).map((snap) => -mathAbs(snap));
  }
  function measureAligned() {
    return groupSlides(snaps).map((g) => g[0]).map((snap, index) => snap + alignments[index]);
  }
  const self = {
    snaps,
    snapsAligned
  };
  return self;
}
function SlideRegistry(containSnaps, containScroll, scrollSnaps, scrollContainLimit, slidesToScroll, slideIndexes) {
  const {
    groupSlides
  } = slidesToScroll;
  const {
    min,
    max
  } = scrollContainLimit;
  const slideRegistry = createSlideRegistry();
  function createSlideRegistry() {
    const groupedSlideIndexes = groupSlides(slideIndexes);
    const doNotContain = !containSnaps || containScroll === "keepSnaps";
    if (scrollSnaps.length === 1)
      return [slideIndexes];
    if (doNotContain)
      return groupedSlideIndexes;
    return groupedSlideIndexes.slice(min, max).map((group, index, groups) => {
      const isFirst = !index;
      const isLast = arrayIsLastIndex(groups, index);
      if (isFirst) {
        const range = arrayLast(groups[0]) + 1;
        return arrayFromNumber(range);
      }
      if (isLast) {
        const range = arrayLastIndex(slideIndexes) - arrayLast(groups)[0] + 1;
        return arrayFromNumber(range, arrayLast(groups)[0]);
      }
      return group;
    });
  }
  const self = {
    slideRegistry
  };
  return self;
}
function ScrollTarget(loop, scrollSnaps, contentSize, limit, targetVector) {
  const {
    reachedAny,
    removeOffset,
    constrain
  } = limit;
  function minDistance(distances) {
    return distances.concat().sort((a2, b2) => mathAbs(a2) - mathAbs(b2))[0];
  }
  function findTargetSnap(target) {
    const distance = loop ? removeOffset(target) : constrain(target);
    const ascDiffsToSnaps = scrollSnaps.map((snap, index2) => ({
      diff: shortcut(snap - distance, 0),
      index: index2
    })).sort((d1, d2) => mathAbs(d1.diff) - mathAbs(d2.diff));
    const {
      index
    } = ascDiffsToSnaps[0];
    return {
      index,
      distance
    };
  }
  function shortcut(target, direction) {
    const targets = [target, target + contentSize, target - contentSize];
    if (!loop)
      return target;
    if (!direction)
      return minDistance(targets);
    const matchingTargets = targets.filter((t2) => mathSign(t2) === direction);
    if (matchingTargets.length)
      return minDistance(matchingTargets);
    return arrayLast(targets) - contentSize;
  }
  function byIndex(index, direction) {
    const diffToSnap = scrollSnaps[index] - targetVector.get();
    const distance = shortcut(diffToSnap, direction);
    return {
      index,
      distance
    };
  }
  function byDistance(distance, snap) {
    const target = targetVector.get() + distance;
    const {
      index,
      distance: targetSnapDistance
    } = findTargetSnap(target);
    const reachedBound = !loop && reachedAny(target);
    if (!snap || reachedBound)
      return {
        index,
        distance
      };
    const diffToSnap = scrollSnaps[index] - targetSnapDistance;
    const snapDistance = distance + shortcut(diffToSnap, 0);
    return {
      index,
      distance: snapDistance
    };
  }
  const self = {
    byDistance,
    byIndex,
    shortcut
  };
  return self;
}
function ScrollTo(animation, indexCurrent, indexPrevious, scrollBody, scrollTarget, targetVector, eventHandler) {
  function scrollTo(target) {
    const distanceDiff = target.distance;
    const indexDiff = target.index !== indexCurrent.get();
    targetVector.add(distanceDiff);
    if (distanceDiff) {
      if (scrollBody.duration()) {
        animation.start();
      } else {
        animation.update();
        animation.render(1);
        animation.update();
      }
    }
    if (indexDiff) {
      indexPrevious.set(indexCurrent.get());
      indexCurrent.set(target.index);
      eventHandler.emit("select");
    }
  }
  function distance(n2, snap) {
    const target = scrollTarget.byDistance(n2, snap);
    scrollTo(target);
  }
  function index(n2, direction) {
    const targetIndex = indexCurrent.clone().set(n2);
    const target = scrollTarget.byIndex(targetIndex.get(), direction);
    scrollTo(target);
  }
  const self = {
    distance,
    index
  };
  return self;
}
function SlideFocus(root, slides, slideRegistry, scrollTo, scrollBody, eventStore, eventHandler, watchFocus) {
  const focusListenerOptions = {
    passive: true,
    capture: true
  };
  let lastTabPressTime = 0;
  function init(emblaApi) {
    if (!watchFocus)
      return;
    function defaultCallback(index) {
      const nowTime = (/* @__PURE__ */ new Date()).getTime();
      const diffTime = nowTime - lastTabPressTime;
      if (diffTime > 10)
        return;
      eventHandler.emit("slideFocusStart");
      root.scrollLeft = 0;
      const group = slideRegistry.findIndex((group2) => group2.includes(index));
      if (!isNumber(group))
        return;
      scrollBody.useDuration(0);
      scrollTo.index(group, 0);
      eventHandler.emit("slideFocus");
    }
    eventStore.add(document, "keydown", registerTabPress, false);
    slides.forEach((slide, slideIndex) => {
      eventStore.add(slide, "focus", (evt) => {
        if (isBoolean(watchFocus) || watchFocus(emblaApi, evt)) {
          defaultCallback(slideIndex);
        }
      }, focusListenerOptions);
    });
  }
  function registerTabPress(event) {
    if (event.code === "Tab")
      lastTabPressTime = (/* @__PURE__ */ new Date()).getTime();
  }
  const self = {
    init
  };
  return self;
}
function Vector1D(initialValue) {
  let value = initialValue;
  function get() {
    return value;
  }
  function set(n2) {
    value = normalizeInput(n2);
  }
  function add(n2) {
    value += normalizeInput(n2);
  }
  function subtract(n2) {
    value -= normalizeInput(n2);
  }
  function normalizeInput(n2) {
    return isNumber(n2) ? n2 : n2.get();
  }
  const self = {
    get,
    set,
    add,
    subtract
  };
  return self;
}
function Translate(axis, container) {
  const translate = axis.scroll === "x" ? x : y2;
  const containerStyle = container.style;
  let previousTarget = null;
  let disabled = false;
  function x(n2) {
    return `translate3d(${n2}px,0px,0px)`;
  }
  function y2(n2) {
    return `translate3d(0px,${n2}px,0px)`;
  }
  function to(target) {
    if (disabled)
      return;
    const newTarget = roundToTwoDecimals(axis.direction(target));
    if (newTarget === previousTarget)
      return;
    containerStyle.transform = translate(newTarget);
    previousTarget = newTarget;
  }
  function toggleActive(active) {
    disabled = !active;
  }
  function clear() {
    if (disabled)
      return;
    containerStyle.transform = "";
    if (!container.getAttribute("style"))
      container.removeAttribute("style");
  }
  const self = {
    clear,
    to,
    toggleActive
  };
  return self;
}
function SlideLooper(axis, viewSize, contentSize, slideSizes, slideSizesWithGaps, snaps, scrollSnaps, location, slides) {
  const roundingSafety = 0.5;
  const ascItems = arrayKeys(slideSizesWithGaps);
  const descItems = arrayKeys(slideSizesWithGaps).reverse();
  const loopPoints = startPoints().concat(endPoints());
  function removeSlideSizes(indexes, from) {
    return indexes.reduce((a2, i2) => {
      return a2 - slideSizesWithGaps[i2];
    }, from);
  }
  function slidesInGap(indexes, gap) {
    return indexes.reduce((a2, i2) => {
      const remainingGap = removeSlideSizes(a2, gap);
      return remainingGap > 0 ? a2.concat([i2]) : a2;
    }, []);
  }
  function findSlideBounds(offset) {
    return snaps.map((snap, index) => ({
      start: snap - slideSizes[index] + roundingSafety + offset,
      end: snap + viewSize - roundingSafety + offset
    }));
  }
  function findLoopPoints(indexes, offset, isEndEdge) {
    const slideBounds = findSlideBounds(offset);
    return indexes.map((index) => {
      const initial = isEndEdge ? 0 : -contentSize;
      const altered = isEndEdge ? contentSize : 0;
      const boundEdge = isEndEdge ? "end" : "start";
      const loopPoint = slideBounds[index][boundEdge];
      return {
        index,
        loopPoint,
        slideLocation: Vector1D(-1),
        translate: Translate(axis, slides[index]),
        target: () => location.get() > loopPoint ? initial : altered
      };
    });
  }
  function startPoints() {
    const gap = scrollSnaps[0];
    const indexes = slidesInGap(descItems, gap);
    return findLoopPoints(indexes, contentSize, false);
  }
  function endPoints() {
    const gap = viewSize - scrollSnaps[0] - 1;
    const indexes = slidesInGap(ascItems, gap);
    return findLoopPoints(indexes, -contentSize, true);
  }
  function canLoop() {
    return loopPoints.every(({
      index
    }) => {
      const otherIndexes = ascItems.filter((i2) => i2 !== index);
      return removeSlideSizes(otherIndexes, viewSize) <= 0.1;
    });
  }
  function loop() {
    loopPoints.forEach((loopPoint) => {
      const {
        target,
        translate,
        slideLocation
      } = loopPoint;
      const shiftLocation = target();
      if (shiftLocation === slideLocation.get())
        return;
      translate.to(shiftLocation);
      slideLocation.set(shiftLocation);
    });
  }
  function clear() {
    loopPoints.forEach((loopPoint) => loopPoint.translate.clear());
  }
  const self = {
    canLoop,
    clear,
    loop,
    loopPoints
  };
  return self;
}
function SlidesHandler(container, eventHandler, watchSlides) {
  let mutationObserver;
  let destroyed = false;
  function init(emblaApi) {
    if (!watchSlides)
      return;
    function defaultCallback(mutations) {
      for (const mutation of mutations) {
        if (mutation.type === "childList") {
          emblaApi.reInit();
          eventHandler.emit("slidesChanged");
          break;
        }
      }
    }
    mutationObserver = new MutationObserver((mutations) => {
      if (destroyed)
        return;
      if (isBoolean(watchSlides) || watchSlides(emblaApi, mutations)) {
        defaultCallback(mutations);
      }
    });
    mutationObserver.observe(container, {
      childList: true
    });
  }
  function destroy() {
    if (mutationObserver)
      mutationObserver.disconnect();
    destroyed = true;
  }
  const self = {
    init,
    destroy
  };
  return self;
}
function SlidesInView(container, slides, eventHandler, threshold) {
  const intersectionEntryMap = {};
  let inViewCache = null;
  let notInViewCache = null;
  let intersectionObserver;
  let destroyed = false;
  function init() {
    intersectionObserver = new IntersectionObserver((entries) => {
      if (destroyed)
        return;
      entries.forEach((entry) => {
        const index = slides.indexOf(entry.target);
        intersectionEntryMap[index] = entry;
      });
      inViewCache = null;
      notInViewCache = null;
      eventHandler.emit("slidesInView");
    }, {
      root: container.parentElement,
      threshold
    });
    slides.forEach((slide) => intersectionObserver.observe(slide));
  }
  function destroy() {
    if (intersectionObserver)
      intersectionObserver.disconnect();
    destroyed = true;
  }
  function createInViewList(inView) {
    return objectKeys(intersectionEntryMap).reduce((list, slideIndex) => {
      const index = parseInt(slideIndex);
      const {
        isIntersecting
      } = intersectionEntryMap[index];
      const inViewMatch = inView && isIntersecting;
      const notInViewMatch = !inView && !isIntersecting;
      if (inViewMatch || notInViewMatch)
        list.push(index);
      return list;
    }, []);
  }
  function get(inView = true) {
    if (inView && inViewCache)
      return inViewCache;
    if (!inView && notInViewCache)
      return notInViewCache;
    const slideIndexes = createInViewList(inView);
    if (inView)
      inViewCache = slideIndexes;
    if (!inView)
      notInViewCache = slideIndexes;
    return slideIndexes;
  }
  const self = {
    init,
    destroy,
    get
  };
  return self;
}
function SlideSizes(axis, containerRect, slideRects, slides, readEdgeGap, ownerWindow) {
  const {
    measureSize,
    startEdge,
    endEdge
  } = axis;
  const withEdgeGap = slideRects[0] && readEdgeGap;
  const startGap = measureStartGap();
  const endGap = measureEndGap();
  const slideSizes = slideRects.map(measureSize);
  const slideSizesWithGaps = measureWithGaps();
  function measureStartGap() {
    if (!withEdgeGap)
      return 0;
    const slideRect = slideRects[0];
    return mathAbs(containerRect[startEdge] - slideRect[startEdge]);
  }
  function measureEndGap() {
    if (!withEdgeGap)
      return 0;
    const style = ownerWindow.getComputedStyle(arrayLast(slides));
    return parseFloat(style.getPropertyValue(`margin-${endEdge}`));
  }
  function measureWithGaps() {
    return slideRects.map((rect, index, rects) => {
      const isFirst = !index;
      const isLast = arrayIsLastIndex(rects, index);
      if (isFirst)
        return slideSizes[index] + startGap;
      if (isLast)
        return slideSizes[index] + endGap;
      return rects[index + 1][startEdge] - rect[startEdge];
    }).map(mathAbs);
  }
  const self = {
    slideSizes,
    slideSizesWithGaps,
    startGap,
    endGap
  };
  return self;
}
function SlidesToScroll(axis, viewSize, slidesToScroll, loop, containerRect, slideRects, startGap, endGap, pixelTolerance) {
  const {
    startEdge,
    endEdge,
    direction
  } = axis;
  const groupByNumber = isNumber(slidesToScroll);
  function byNumber(array, groupSize) {
    return arrayKeys(array).filter((i2) => i2 % groupSize === 0).map((i2) => array.slice(i2, i2 + groupSize));
  }
  function bySize(array) {
    if (!array.length)
      return [];
    return arrayKeys(array).reduce((groups, rectB, index) => {
      const rectA = arrayLast(groups) || 0;
      const isFirst = rectA === 0;
      const isLast = rectB === arrayLastIndex(array);
      const edgeA = containerRect[startEdge] - slideRects[rectA][startEdge];
      const edgeB = containerRect[startEdge] - slideRects[rectB][endEdge];
      const gapA = !loop && isFirst ? direction(startGap) : 0;
      const gapB = !loop && isLast ? direction(endGap) : 0;
      const chunkSize = mathAbs(edgeB - gapB - (edgeA + gapA));
      if (index && chunkSize > viewSize + pixelTolerance)
        groups.push(rectB);
      if (isLast)
        groups.push(array.length);
      return groups;
    }, []).map((currentSize, index, groups) => {
      const previousSize = Math.max(groups[index - 1] || 0);
      return array.slice(previousSize, currentSize);
    });
  }
  function groupSlides(array) {
    return groupByNumber ? byNumber(array, slidesToScroll) : bySize(array);
  }
  const self = {
    groupSlides
  };
  return self;
}
function Engine(root, container, slides, ownerDocument, ownerWindow, options, eventHandler) {
  const {
    align,
    axis: scrollAxis,
    direction,
    startIndex,
    loop,
    duration,
    dragFree,
    dragThreshold,
    inViewThreshold,
    slidesToScroll: groupSlides,
    skipSnaps,
    containScroll,
    watchResize,
    watchSlides,
    watchDrag,
    watchFocus
  } = options;
  const pixelTolerance = 2;
  const nodeRects = NodeRects();
  const containerRect = nodeRects.measure(container);
  const slideRects = slides.map(nodeRects.measure);
  const axis = Axis(scrollAxis, direction);
  const viewSize = axis.measureSize(containerRect);
  const percentOfView = PercentOfView(viewSize);
  const alignment = Alignment(align, viewSize);
  const containSnaps = !loop && !!containScroll;
  const readEdgeGap = loop || !!containScroll;
  const {
    slideSizes,
    slideSizesWithGaps,
    startGap,
    endGap
  } = SlideSizes(axis, containerRect, slideRects, slides, readEdgeGap, ownerWindow);
  const slidesToScroll = SlidesToScroll(axis, viewSize, groupSlides, loop, containerRect, slideRects, startGap, endGap, pixelTolerance);
  const {
    snaps,
    snapsAligned
  } = ScrollSnaps(axis, alignment, containerRect, slideRects, slidesToScroll);
  const contentSize = -arrayLast(snaps) + arrayLast(slideSizesWithGaps);
  const {
    snapsContained,
    scrollContainLimit
  } = ScrollContain(viewSize, contentSize, snapsAligned, containScroll, pixelTolerance);
  const scrollSnaps = containSnaps ? snapsContained : snapsAligned;
  const {
    limit
  } = ScrollLimit(contentSize, scrollSnaps, loop);
  const index = Counter(arrayLastIndex(scrollSnaps), startIndex, loop);
  const indexPrevious = index.clone();
  const slideIndexes = arrayKeys(slides);
  const update = ({
    dragHandler,
    scrollBody: scrollBody2,
    scrollBounds,
    options: {
      loop: loop2
    }
  }) => {
    if (!loop2)
      scrollBounds.constrain(dragHandler.pointerDown());
    scrollBody2.seek();
  };
  const render = ({
    scrollBody: scrollBody2,
    translate,
    location: location2,
    offsetLocation: offsetLocation2,
    previousLocation: previousLocation2,
    scrollLooper,
    slideLooper,
    dragHandler,
    animation: animation2,
    eventHandler: eventHandler2,
    scrollBounds,
    options: {
      loop: loop2
    }
  }, alpha) => {
    const shouldSettle = scrollBody2.settled();
    const withinBounds = !scrollBounds.shouldConstrain();
    const hasSettled = loop2 ? shouldSettle : shouldSettle && withinBounds;
    if (hasSettled && !dragHandler.pointerDown()) {
      animation2.stop();
      eventHandler2.emit("settle");
    }
    if (!hasSettled)
      eventHandler2.emit("scroll");
    const interpolatedLocation = location2.get() * alpha + previousLocation2.get() * (1 - alpha);
    offsetLocation2.set(interpolatedLocation);
    if (loop2) {
      scrollLooper.loop(scrollBody2.direction());
      slideLooper.loop();
    }
    translate.to(offsetLocation2.get());
  };
  const animation = Animations(ownerDocument, ownerWindow, () => update(engine), (alpha) => render(engine, alpha));
  const friction = 0.68;
  const startLocation = scrollSnaps[index.get()];
  const location = Vector1D(startLocation);
  const previousLocation = Vector1D(startLocation);
  const offsetLocation = Vector1D(startLocation);
  const target = Vector1D(startLocation);
  const scrollBody = ScrollBody(location, offsetLocation, previousLocation, target, duration, friction);
  const scrollTarget = ScrollTarget(loop, scrollSnaps, contentSize, limit, target);
  const scrollTo = ScrollTo(animation, index, indexPrevious, scrollBody, scrollTarget, target, eventHandler);
  const scrollProgress = ScrollProgress(limit);
  const eventStore = EventStore();
  const slidesInView = SlidesInView(container, slides, eventHandler, inViewThreshold);
  const {
    slideRegistry
  } = SlideRegistry(containSnaps, containScroll, scrollSnaps, scrollContainLimit, slidesToScroll, slideIndexes);
  const slideFocus = SlideFocus(root, slides, slideRegistry, scrollTo, scrollBody, eventStore, eventHandler, watchFocus);
  const engine = {
    ownerDocument,
    ownerWindow,
    eventHandler,
    containerRect,
    slideRects,
    animation,
    axis,
    dragHandler: DragHandler(axis, root, ownerDocument, ownerWindow, target, DragTracker(axis, ownerWindow), location, animation, scrollTo, scrollBody, scrollTarget, index, eventHandler, percentOfView, dragFree, dragThreshold, skipSnaps, friction, watchDrag),
    eventStore,
    percentOfView,
    index,
    indexPrevious,
    limit,
    location,
    offsetLocation,
    previousLocation,
    options,
    resizeHandler: ResizeHandler(container, eventHandler, ownerWindow, slides, axis, watchResize, nodeRects),
    scrollBody,
    scrollBounds: ScrollBounds(limit, offsetLocation, target, scrollBody, percentOfView),
    scrollLooper: ScrollLooper(contentSize, limit, offsetLocation, [location, offsetLocation, previousLocation, target]),
    scrollProgress,
    scrollSnapList: scrollSnaps.map(scrollProgress.get),
    scrollSnaps,
    scrollTarget,
    scrollTo,
    slideLooper: SlideLooper(axis, viewSize, contentSize, slideSizes, slideSizesWithGaps, snaps, scrollSnaps, offsetLocation, slides),
    slideFocus,
    slidesHandler: SlidesHandler(container, eventHandler, watchSlides),
    slidesInView,
    slideIndexes,
    slideRegistry,
    slidesToScroll,
    target,
    translate: Translate(axis, container)
  };
  return engine;
}
function EventHandler() {
  let listeners = {};
  let api;
  function init(emblaApi) {
    api = emblaApi;
  }
  function getListeners(evt) {
    return listeners[evt] || [];
  }
  function emit(evt) {
    getListeners(evt).forEach((e2) => e2(api, evt));
    return self;
  }
  function on(evt, cb) {
    listeners[evt] = getListeners(evt).concat([cb]);
    return self;
  }
  function off(evt, cb) {
    listeners[evt] = getListeners(evt).filter((e2) => e2 !== cb);
    return self;
  }
  function clear() {
    listeners = {};
  }
  const self = {
    init,
    emit,
    off,
    on,
    clear
  };
  return self;
}
var defaultOptions = {
  align: "center",
  axis: "x",
  container: null,
  slides: null,
  containScroll: "trimSnaps",
  direction: "ltr",
  slidesToScroll: 1,
  inViewThreshold: 0,
  breakpoints: {},
  dragFree: false,
  dragThreshold: 10,
  loop: false,
  skipSnaps: false,
  duration: 25,
  startIndex: 0,
  active: true,
  watchDrag: true,
  watchResize: true,
  watchSlides: true,
  watchFocus: true
};
function OptionsHandler(ownerWindow) {
  function mergeOptions(optionsA, optionsB) {
    return objectsMergeDeep(optionsA, optionsB || {});
  }
  function optionsAtMedia(options) {
    const optionsAtMedia2 = options.breakpoints || {};
    const matchedMediaOptions = objectKeys(optionsAtMedia2).filter((media) => ownerWindow.matchMedia(media).matches).map((media) => optionsAtMedia2[media]).reduce((a2, mediaOption) => mergeOptions(a2, mediaOption), {});
    return mergeOptions(options, matchedMediaOptions);
  }
  function optionsMediaQueries(optionsList) {
    return optionsList.map((options) => objectKeys(options.breakpoints || {})).reduce((acc, mediaQueries) => acc.concat(mediaQueries), []).map(ownerWindow.matchMedia);
  }
  const self = {
    mergeOptions,
    optionsAtMedia,
    optionsMediaQueries
  };
  return self;
}
function PluginsHandler(optionsHandler) {
  let activePlugins = [];
  function init(emblaApi, plugins) {
    activePlugins = plugins.filter(({
      options
    }) => optionsHandler.optionsAtMedia(options).active !== false);
    activePlugins.forEach((plugin) => plugin.init(emblaApi, optionsHandler));
    return plugins.reduce((map, plugin) => Object.assign(map, {
      [plugin.name]: plugin
    }), {});
  }
  function destroy() {
    activePlugins = activePlugins.filter((plugin) => plugin.destroy());
  }
  const self = {
    init,
    destroy
  };
  return self;
}
function EmblaCarousel(root, userOptions, userPlugins) {
  const ownerDocument = root.ownerDocument;
  const ownerWindow = ownerDocument.defaultView;
  const optionsHandler = OptionsHandler(ownerWindow);
  const pluginsHandler = PluginsHandler(optionsHandler);
  const mediaHandlers = EventStore();
  const eventHandler = EventHandler();
  const {
    mergeOptions,
    optionsAtMedia,
    optionsMediaQueries
  } = optionsHandler;
  const {
    on,
    off,
    emit
  } = eventHandler;
  const reInit = reActivate;
  let destroyed = false;
  let engine;
  let optionsBase = mergeOptions(defaultOptions, EmblaCarousel.globalOptions);
  let options = mergeOptions(optionsBase);
  let pluginList = [];
  let pluginApis;
  let container;
  let slides;
  function storeElements() {
    const {
      container: userContainer,
      slides: userSlides
    } = options;
    const customContainer = isString(userContainer) ? root.querySelector(userContainer) : userContainer;
    container = customContainer || root.children[0];
    const customSlides = isString(userSlides) ? container.querySelectorAll(userSlides) : userSlides;
    slides = [].slice.call(customSlides || container.children);
  }
  function createEngine(options2) {
    const engine2 = Engine(root, container, slides, ownerDocument, ownerWindow, options2, eventHandler);
    if (options2.loop && !engine2.slideLooper.canLoop()) {
      const optionsWithoutLoop = Object.assign({}, options2, {
        loop: false
      });
      return createEngine(optionsWithoutLoop);
    }
    return engine2;
  }
  function activate(withOptions, withPlugins) {
    if (destroyed)
      return;
    optionsBase = mergeOptions(optionsBase, withOptions);
    options = optionsAtMedia(optionsBase);
    pluginList = withPlugins || pluginList;
    storeElements();
    engine = createEngine(options);
    optionsMediaQueries([optionsBase, ...pluginList.map(({
      options: options2
    }) => options2)]).forEach((query) => mediaHandlers.add(query, "change", reActivate));
    if (!options.active)
      return;
    engine.translate.to(engine.location.get());
    engine.animation.init();
    engine.slidesInView.init();
    engine.slideFocus.init(self);
    engine.eventHandler.init(self);
    engine.resizeHandler.init(self);
    engine.slidesHandler.init(self);
    if (engine.options.loop)
      engine.slideLooper.loop();
    if (container.offsetParent && slides.length)
      engine.dragHandler.init(self);
    pluginApis = pluginsHandler.init(self, pluginList);
  }
  function reActivate(withOptions, withPlugins) {
    const startIndex = selectedScrollSnap();
    deActivate();
    activate(mergeOptions({
      startIndex
    }, withOptions), withPlugins);
    eventHandler.emit("reInit");
  }
  function deActivate() {
    engine.dragHandler.destroy();
    engine.eventStore.clear();
    engine.translate.clear();
    engine.slideLooper.clear();
    engine.resizeHandler.destroy();
    engine.slidesHandler.destroy();
    engine.slidesInView.destroy();
    engine.animation.destroy();
    pluginsHandler.destroy();
    mediaHandlers.clear();
  }
  function destroy() {
    if (destroyed)
      return;
    destroyed = true;
    mediaHandlers.clear();
    deActivate();
    eventHandler.emit("destroy");
    eventHandler.clear();
  }
  function scrollTo(index, jump, direction) {
    if (!options.active || destroyed)
      return;
    engine.scrollBody.useBaseFriction().useDuration(jump === true ? 0 : options.duration);
    engine.scrollTo.index(index, direction || 0);
  }
  function scrollNext(jump) {
    const next = engine.index.add(1).get();
    scrollTo(next, jump, -1);
  }
  function scrollPrev(jump) {
    const prev = engine.index.add(-1).get();
    scrollTo(prev, jump, 1);
  }
  function canScrollNext() {
    const next = engine.index.add(1).get();
    return next !== selectedScrollSnap();
  }
  function canScrollPrev() {
    const prev = engine.index.add(-1).get();
    return prev !== selectedScrollSnap();
  }
  function scrollSnapList() {
    return engine.scrollSnapList;
  }
  function scrollProgress() {
    return engine.scrollProgress.get(engine.location.get());
  }
  function selectedScrollSnap() {
    return engine.index.get();
  }
  function previousScrollSnap() {
    return engine.indexPrevious.get();
  }
  function slidesInView() {
    return engine.slidesInView.get();
  }
  function slidesNotInView() {
    return engine.slidesInView.get(false);
  }
  function plugins() {
    return pluginApis;
  }
  function internalEngine() {
    return engine;
  }
  function rootNode() {
    return root;
  }
  function containerNode() {
    return container;
  }
  function slideNodes() {
    return slides;
  }
  const self = {
    canScrollNext,
    canScrollPrev,
    containerNode,
    internalEngine,
    destroy,
    off,
    on,
    emit,
    plugins,
    previousScrollSnap,
    reInit,
    rootNode,
    scrollNext,
    scrollPrev,
    scrollProgress,
    scrollSnapList,
    scrollTo,
    selectedScrollSnap,
    slideNodes,
    slidesInView,
    slidesNotInView
  };
  activate(userOptions, userPlugins);
  setTimeout(() => eventHandler.emit("init"), 0);
  return self;
}
EmblaCarousel.globalOptions = void 0;

// node_modules/.pnpm/embla-carousel-react@8.5.2_react@18.3.1/node_modules/embla-carousel-react/esm/embla-carousel-react.esm.js
function useEmblaCarousel(options = {}, plugins = []) {
  const storedOptions = (0, import_react.useRef)(options);
  const storedPlugins = (0, import_react.useRef)(plugins);
  const [emblaApi, setEmblaApi] = (0, import_react.useState)();
  const [viewport, setViewport] = (0, import_react.useState)();
  const reInit = (0, import_react.useCallback)(() => {
    if (emblaApi)
      emblaApi.reInit(storedOptions.current, storedPlugins.current);
  }, [emblaApi]);
  (0, import_react.useEffect)(() => {
    if (areOptionsEqual(storedOptions.current, options))
      return;
    storedOptions.current = options;
    reInit();
  }, [options, reInit]);
  (0, import_react.useEffect)(() => {
    if (arePluginsEqual(storedPlugins.current, plugins))
      return;
    storedPlugins.current = plugins;
    reInit();
  }, [plugins, reInit]);
  (0, import_react.useEffect)(() => {
    if (canUseDOM() && viewport) {
      EmblaCarousel.globalOptions = useEmblaCarousel.globalOptions;
      const newEmblaApi = EmblaCarousel(viewport, storedOptions.current, storedPlugins.current);
      setEmblaApi(newEmblaApi);
      return () => newEmblaApi.destroy();
    } else {
      setEmblaApi(void 0);
    }
  }, [viewport, setEmblaApi]);
  return [setViewport, emblaApi];
}
useEmblaCarousel.globalOptions = void 0;

// app/components/ui/carousel.tsx
var import_jsx_dev_runtime = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/components/ui/carousel.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
var _s = $RefreshSig$();
var _s2 = $RefreshSig$();
var _s3 = $RefreshSig$();
var _s4 = $RefreshSig$();
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/components/ui/carousel.tsx"
  );
  import.meta.hot.lastModified = "1738662837906.6753";
}
var CarouselContext = React.createContext(null);
function useCarousel() {
  _s();
  const context = React.useContext(CarouselContext);
  if (!context) {
    throw new Error("useCarousel must be used within a <Carousel />");
  }
  return context;
}
_s(useCarousel, "b9L3QQ+jgeyIrH0NfHrJ8nn7VMU=");
var Carousel = _s2(React.forwardRef(_c = _s2(({
  orientation = "horizontal",
  opts,
  setApi,
  plugins,
  className,
  children,
  ...props
}, ref) => {
  _s2();
  const [carouselRef, api] = useEmblaCarousel({
    ...opts,
    axis: orientation === "horizontal" ? "x" : "y"
  }, plugins);
  const [canScrollPrev, setCanScrollPrev] = React.useState(false);
  const [canScrollNext, setCanScrollNext] = React.useState(false);
  const onSelect = React.useCallback((api2) => {
    if (!api2) {
      return;
    }
    setCanScrollPrev(api2.canScrollPrev());
    setCanScrollNext(api2.canScrollNext());
  }, []);
  const scrollPrev = React.useCallback(() => {
    api?.scrollPrev();
  }, [api]);
  const scrollNext = React.useCallback(() => {
    api?.scrollNext();
  }, [api]);
  const onInit = React.useCallback((api2) => {
    if (!api2) {
      return;
    }
  }, []);
  React.useEffect(() => {
    if (!api || !setApi) {
      return;
    }
    setApi(api);
  }, [api, setApi]);
  React.useEffect(() => {
    if (!api) {
      return;
    }
    onInit(api);
    onSelect(api);
    api.on("reInit", onInit);
    api.on("select", onSelect);
    return () => {
      api?.off("select", onSelect);
    };
  }, [api, onInit, onSelect]);
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)(CarouselContext.Provider, { value: {
    carouselRef,
    api,
    opts,
    orientation: orientation || (opts?.axis === "y" ? "vertical" : "horizontal"),
    scrollPrev,
    scrollNext,
    canScrollPrev,
    canScrollNext
  }, children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { ref, className: cn("relative", className), role: "region", "aria-roledescription": "carousel", ...props, children }, void 0, false, {
    fileName: "app/components/ui/carousel.tsx",
    lineNumber: 100,
    columnNumber: 9
  }, this) }, void 0, false, {
    fileName: "app/components/ui/carousel.tsx",
    lineNumber: 90,
    columnNumber: 10
  }, this);
}, "6uX6kjgWbB5hjyMnb8ywA/v/bwc=", false, function() {
  return [useEmblaCarousel];
})), "6uX6kjgWbB5hjyMnb8ywA/v/bwc=", false, function() {
  return [useEmblaCarousel];
});
_c2 = Carousel;
Carousel.displayName = "Carousel";
var CarouselContent = _s3(React.forwardRef(_c3 = _s3(({
  className,
  ...props
}, ref) => {
  _s3();
  const {
    carouselRef,
    orientation
  } = useCarousel();
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { ref: carouselRef, className: "overflow-hidden", children: /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { ref, className: cn("flex", orientation === "horizontal" ? "-ml-4" : "-mt-4 flex-col", className), ...props }, void 0, false, {
    fileName: "app/components/ui/carousel.tsx",
    lineNumber: 121,
    columnNumber: 7
  }, this) }, void 0, false, {
    fileName: "app/components/ui/carousel.tsx",
    lineNumber: 120,
    columnNumber: 10
  }, this);
}, "YNqN7/p8l2NfYueiPechI4IqsYo=", false, function() {
  return [useCarousel];
})), "YNqN7/p8l2NfYueiPechI4IqsYo=", false, function() {
  return [useCarousel];
});
_c4 = CarouselContent;
CarouselContent.displayName = "CarouselContent";
var CarouselItem = _s4(React.forwardRef(_c5 = _s4(({
  className,
  ...props
}, ref) => {
  _s4();
  const {
    orientation
  } = useCarousel();
  return /* @__PURE__ */ (0, import_jsx_dev_runtime.jsxDEV)("div", { ref, role: "group", "aria-roledescription": "slide", className: cn("min-w-0 shrink-0 grow-0 basis-full", orientation === "horizontal" ? "pl-4" : "pt-4", className), ...props }, void 0, false, {
    fileName: "app/components/ui/carousel.tsx",
    lineNumber: 138,
    columnNumber: 10
  }, this);
}, "bPPpMbUdjWnfcwMzP4altEp5ZJs=", false, function() {
  return [useCarousel];
})), "bPPpMbUdjWnfcwMzP4altEp5ZJs=", false, function() {
  return [useCarousel];
});
_c6 = CarouselItem;
CarouselItem.displayName = "CarouselItem";
var _c;
var _c2;
var _c3;
var _c4;
var _c5;
var _c6;
$RefreshReg$(_c, "Carousel$React.forwardRef");
$RefreshReg$(_c2, "Carousel");
$RefreshReg$(_c3, "CarouselContent$React.forwardRef");
$RefreshReg$(_c4, "CarouselContent");
$RefreshReg$(_c5, "CarouselItem$React.forwardRef");
$RefreshReg$(_c6, "CarouselItem");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;

// node_modules/.pnpm/react-type-animation@3.2.0_prop-types@15.8.1_react-dom@18.3.1_react@18.3.1__react@18.3.1/node_modules/react-type-animation/dist/esm/index.es.js
var import_react2 = __toESM(require_react());
function i(e2, t2, r2, n2) {
  return new (r2 || (r2 = Promise))(function(o2, a2) {
    function i2(e3) {
      try {
        c2(n2.next(e3));
      } catch (e4) {
        a2(e4);
      }
    }
    function u2(e3) {
      try {
        c2(n2.throw(e3));
      } catch (e4) {
        a2(e4);
      }
    }
    function c2(e3) {
      var t3;
      e3.done ? o2(e3.value) : (t3 = e3.value, t3 instanceof r2 ? t3 : new r2(function(e4) {
        e4(t3);
      })).then(i2, u2);
    }
    c2((n2 = n2.apply(e2, t2 || [])).next());
  });
}
function u(e2, t2) {
  var r2, n2, o2, a2, i2 = { label: 0, sent: function() {
    if (1 & o2[0])
      throw o2[1];
    return o2[1];
  }, trys: [], ops: [] };
  return a2 = { next: u2(0), throw: u2(1), return: u2(2) }, "function" == typeof Symbol && (a2[Symbol.iterator] = function() {
    return this;
  }), a2;
  function u2(a3) {
    return function(u3) {
      return function(a4) {
        if (r2)
          throw new TypeError("Generator is already executing.");
        for (; i2; )
          try {
            if (r2 = 1, n2 && (o2 = 2 & a4[0] ? n2.return : a4[0] ? n2.throw || ((o2 = n2.return) && o2.call(n2), 0) : n2.next) && !(o2 = o2.call(n2, a4[1])).done)
              return o2;
            switch (n2 = 0, o2 && (a4 = [2 & a4[0], o2.value]), a4[0]) {
              case 0:
              case 1:
                o2 = a4;
                break;
              case 4:
                return i2.label++, { value: a4[1], done: false };
              case 5:
                i2.label++, n2 = a4[1], a4 = [0];
                continue;
              case 7:
                a4 = i2.ops.pop(), i2.trys.pop();
                continue;
              default:
                if (!(o2 = i2.trys, (o2 = o2.length > 0 && o2[o2.length - 1]) || 6 !== a4[0] && 2 !== a4[0])) {
                  i2 = 0;
                  continue;
                }
                if (3 === a4[0] && (!o2 || a4[1] > o2[0] && a4[1] < o2[3])) {
                  i2.label = a4[1];
                  break;
                }
                if (6 === a4[0] && i2.label < o2[1]) {
                  i2.label = o2[1], o2 = a4;
                  break;
                }
                if (o2 && i2.label < o2[2]) {
                  i2.label = o2[2], i2.ops.push(a4);
                  break;
                }
                o2[2] && i2.ops.pop(), i2.trys.pop();
                continue;
            }
            a4 = t2.call(e2, i2);
          } catch (e3) {
            a4 = [6, e3], n2 = 0;
          } finally {
            r2 = o2 = 0;
          }
        if (5 & a4[0])
          throw a4[1];
        return { value: a4[0] ? a4[1] : void 0, done: true };
      }([a3, u3]);
    };
  }
}
function c(e2) {
  var t2 = "function" == typeof Symbol && Symbol.iterator, r2 = t2 && e2[t2], n2 = 0;
  if (r2)
    return r2.call(e2);
  if (e2 && "number" == typeof e2.length)
    return { next: function() {
      return e2 && n2 >= e2.length && (e2 = void 0), { value: e2 && e2[n2++], done: !e2 };
    } };
  throw new TypeError(t2 ? "Object is not iterable." : "Symbol.iterator is not defined.");
}
function l(e2, t2) {
  var r2 = "function" == typeof Symbol && e2[Symbol.iterator];
  if (!r2)
    return e2;
  var n2, o2, a2 = r2.call(e2), i2 = [];
  try {
    for (; (void 0 === t2 || t2-- > 0) && !(n2 = a2.next()).done; )
      i2.push(n2.value);
  } catch (e3) {
    o2 = { error: e3 };
  } finally {
    try {
      n2 && !n2.done && (r2 = a2.return) && r2.call(a2);
    } finally {
      if (o2)
        throw o2.error;
    }
  }
  return i2;
}
function s(e2, t2, r2) {
  if (r2 || 2 === arguments.length)
    for (var n2, o2 = 0, a2 = t2.length; o2 < a2; o2++)
      !n2 && o2 in t2 || (n2 || (n2 = Array.prototype.slice.call(t2, 0, o2)), n2[o2] = t2[o2]);
  return e2.concat(n2 || Array.prototype.slice.call(t2));
}
function f(e2, t2, r2, n2, o2) {
  for (var a2 = [], f2 = 5; f2 < arguments.length; f2++)
    a2[f2 - 5] = arguments[f2];
  return i(this, void 0, void 0, function() {
    var i2, f3, h2, y2, v2, b2;
    return u(this, function(u2) {
      switch (u2.label) {
        case 0:
          u2.trys.push([0, 12, 13, 14]), i2 = c(a2), f3 = i2.next(), u2.label = 1;
        case 1:
          if (f3.done)
            return [3, 11];
          switch (h2 = f3.value, typeof h2) {
            case "string":
              return [3, 2];
            case "number":
              return [3, 4];
            case "function":
              return [3, 6];
          }
          return [3, 8];
        case 2:
          return [4, d(e2, t2, h2, r2, n2, o2)];
        case 3:
          return u2.sent(), [3, 10];
        case 4:
          return [4, p(h2)];
        case 5:
          return u2.sent(), [3, 10];
        case 6:
          return [4, h2.apply(void 0, s([e2, t2, r2, n2, o2], l(a2), false))];
        case 7:
          return u2.sent(), [3, 10];
        case 8:
          return [4, h2];
        case 9:
          u2.sent(), u2.label = 10;
        case 10:
          return f3 = i2.next(), [3, 1];
        case 11:
          return [3, 14];
        case 12:
          return y2 = u2.sent(), v2 = { error: y2 }, [3, 14];
        case 13:
          try {
            f3 && !f3.done && (b2 = i2.return) && b2.call(i2);
          } finally {
            if (v2)
              throw v2.error;
          }
          return [7];
        case 14:
          return [2];
      }
    });
  });
}
function d(e2, t2, r2, n2, o2, a2) {
  return i(this, void 0, void 0, function() {
    var i2, c2;
    return u(this, function(u2) {
      switch (u2.label) {
        case 0:
          return i2 = e2.textContent || "", c2 = function(e3, t3) {
            var r3 = l(t3).slice(0);
            return s(s([], l(e3), false), [NaN], false).findIndex(function(e4, t4) {
              return r3[t4] !== e4;
            });
          }(i2, r2), [4, h(e2, s(s([], l(v(i2, t2, c2)), false), l(y(r2, t2, c2)), false), n2, o2, a2)];
        case 1:
          return u2.sent(), [2];
      }
    });
  });
}
function p(e2) {
  return i(this, void 0, void 0, function() {
    return u(this, function(t2) {
      switch (t2.label) {
        case 0:
          return [4, new Promise(function(t3) {
            return setTimeout(t3, e2);
          })];
        case 1:
          return t2.sent(), [2];
      }
    });
  });
}
function h(e2, t2, r2, n2, o2) {
  return i(this, void 0, void 0, function() {
    var a2, i2, s2, f2, d2, h2, y2, v2, b2, m2, w, g, x;
    return u(this, function(S) {
      switch (S.label) {
        case 0:
          if (a2 = t2, o2) {
            for (i2 = 0, s2 = 1; s2 < t2.length; s2++)
              if (f2 = l([t2[s2 - 1], t2[s2]], 2), d2 = f2[0], (h2 = f2[1]).length > d2.length || "" === h2) {
                i2 = s2;
                break;
              }
            a2 = t2.slice(i2, t2.length);
          }
          S.label = 1;
        case 1:
          S.trys.push([1, 6, 7, 8]), y2 = c(function(e3) {
            var t3, r3, n3, o3, a3, i3, l2;
            return u(this, function(s3) {
              switch (s3.label) {
                case 0:
                  t3 = function(e4) {
                    return u(this, function(t4) {
                      switch (t4.label) {
                        case 0:
                          return [4, { op: function(t5) {
                            return requestAnimationFrame(function() {
                              return t5.textContent = e4;
                            });
                          }, opCode: function(t5) {
                            var r4 = t5.textContent || "";
                            return "" === e4 || r4.length > e4.length ? "DELETE" : "WRITING";
                          } }];
                        case 1:
                          return t4.sent(), [2];
                      }
                    });
                  }, s3.label = 1;
                case 1:
                  s3.trys.push([1, 6, 7, 8]), r3 = c(e3), n3 = r3.next(), s3.label = 2;
                case 2:
                  return n3.done ? [3, 5] : (o3 = n3.value, [5, t3(o3)]);
                case 3:
                  s3.sent(), s3.label = 4;
                case 4:
                  return n3 = r3.next(), [3, 2];
                case 5:
                  return [3, 8];
                case 6:
                  return a3 = s3.sent(), i3 = { error: a3 }, [3, 8];
                case 7:
                  try {
                    n3 && !n3.done && (l2 = r3.return) && l2.call(r3);
                  } finally {
                    if (i3)
                      throw i3.error;
                  }
                  return [7];
                case 8:
                  return [2];
              }
            });
          }(a2)), v2 = y2.next(), S.label = 2;
        case 2:
          return v2.done ? [3, 5] : (b2 = v2.value, m2 = "WRITING" === b2.opCode(e2) ? r2 + r2 * (Math.random() - 0.5) : n2 + n2 * (Math.random() - 0.5), b2.op(e2), [4, p(m2)]);
        case 3:
          S.sent(), S.label = 4;
        case 4:
          return v2 = y2.next(), [3, 2];
        case 5:
          return [3, 8];
        case 6:
          return w = S.sent(), g = { error: w }, [3, 8];
        case 7:
          try {
            v2 && !v2.done && (x = y2.return) && x.call(y2);
          } finally {
            if (g)
              throw g.error;
          }
          return [7];
        case 8:
          return [2];
      }
    });
  });
}
function y(e2, t2, r2) {
  var n2, o2;
  return void 0 === r2 && (r2 = 0), u(this, function(a2) {
    switch (a2.label) {
      case 0:
        n2 = t2(e2), o2 = n2.length, a2.label = 1;
      case 1:
        return r2 < o2 ? [4, n2.slice(0, ++r2).join("")] : [3, 3];
      case 2:
        return a2.sent(), [3, 1];
      case 3:
        return [2];
    }
  });
}
function v(e2, t2, r2) {
  var n2, o2;
  return void 0 === r2 && (r2 = 0), u(this, function(a2) {
    switch (a2.label) {
      case 0:
        n2 = t2(e2), o2 = n2.length, a2.label = 1;
      case 1:
        return o2 > r2 ? [4, n2.slice(0, --o2).join("")] : [3, 3];
      case 2:
        return a2.sent(), [3, 1];
      case 3:
        return [2];
    }
  });
}
var b = "index-module_type__E-SaG";
!function(e2, t2) {
  void 0 === t2 && (t2 = {});
  var r2 = t2.insertAt;
  if (e2 && "undefined" != typeof document) {
    var n2 = document.head || document.getElementsByTagName("head")[0], o2 = document.createElement("style");
    o2.type = "text/css", "top" === r2 && n2.firstChild ? n2.insertBefore(o2, n2.firstChild) : n2.appendChild(o2), o2.styleSheet ? o2.styleSheet.cssText = e2 : o2.appendChild(document.createTextNode(e2));
  }
}(".index-module_type__E-SaG::after {\n  content: '|';\n  animation: index-module_cursor__PQg0P 1.1s infinite step-start;\n}\n\n@keyframes index-module_cursor__PQg0P {\n  50% {\n    opacity: 0;\n  }\n}\n");
var m = (0, import_react2.memo)((0, import_react2.forwardRef)(function(o2, a2) {
  var i2 = o2.sequence, u2 = o2.repeat, c2 = o2.className, d2 = o2.speed, p2 = void 0 === d2 ? 40 : d2, h2 = o2.deletionSpeed, y2 = o2.omitDeletionAnimation, v2 = void 0 !== y2 && y2, m2 = o2.preRenderFirstString, w = void 0 !== m2 && m2, g = o2.wrapper, x = void 0 === g ? "span" : g, S = o2.splitter, E = void 0 === S ? function(e2) {
    return s([], l(e2), false);
  } : S, _ = o2.cursor, k = void 0 === _ || _, O = o2.style, T = function(e2, t2) {
    var r2 = {};
    for (var n2 in e2)
      Object.prototype.hasOwnProperty.call(e2, n2) && t2.indexOf(n2) < 0 && (r2[n2] = e2[n2]);
    if (null != e2 && "function" == typeof Object.getOwnPropertySymbols) {
      var o3 = 0;
      for (n2 = Object.getOwnPropertySymbols(e2); o3 < n2.length; o3++)
        t2.indexOf(n2[o3]) < 0 && Object.prototype.propertyIsEnumerable.call(e2, n2[o3]) && (r2[n2[o3]] = e2[n2[o3]]);
    }
    return r2;
  }(o2, ["sequence", "repeat", "className", "speed", "deletionSpeed", "omitDeletionAnimation", "preRenderFirstString", "wrapper", "splitter", "cursor", "style"]), A = T["aria-label"], C = T["aria-hidden"], N = T.role;
  h2 || (h2 = p2);
  var P = new Array(2).fill(40);
  [p2, h2].forEach(function(e2, t2) {
    switch (typeof e2) {
      case "number":
        P[t2] = Math.abs(e2 - 100);
        break;
      case "object":
        var r2 = e2.type, n2 = e2.value;
        if ("number" != typeof n2)
          break;
        if ("keyStrokeDelayInMs" === r2)
          P[t2] = n2;
    }
  });
  var j, I, G, D, M, R, q = P[0], F = P[1], B = function(e2, r2) {
    void 0 === r2 && (r2 = null);
    var o3 = (0, import_react2.useRef)(r2);
    return (0, import_react2.useEffect)(function() {
      e2 && ("function" == typeof e2 ? e2(o3.current) : e2.current = o3.current);
    }, [e2]), o3;
  }(a2), Q = b;
  j = c2 ? "".concat(k ? Q + " " : "").concat(c2) : k ? Q : "", I = (0, import_react2.useRef)(function() {
    var e2, t2 = i2;
    u2 === 1 / 0 ? e2 = f : "number" == typeof u2 && (t2 = Array(1 + u2).fill(i2).flat());
    var r2 = e2 ? s(s([], l(t2), false), [e2], false) : s([], l(t2), false);
    return f.apply(void 0, s([B.current, E, q, F, v2], l(r2), false)), function() {
      B.current;
    };
  }), G = (0, import_react2.useRef)(), D = (0, import_react2.useRef)(false), M = (0, import_react2.useRef)(false), R = l((0, import_react2.useState)(0), 2)[1], D.current && (M.current = true), (0, import_react2.useEffect)(function() {
    return D.current || (G.current = I.current(), D.current = true), R(function(e2) {
      return e2 + 1;
    }), function() {
      M.current && G.current && G.current();
    };
  }, []);
  var W = x, L = w ? i2.find(function(e2) {
    return "string" == typeof e2;
  }) || "" : null;
  return import_react2.default.createElement(W, { "aria-hidden": C, "aria-label": A, role: N, style: O, className: j, children: A ? import_react2.default.createElement("span", { "aria-hidden": "true", ref: B, children: L }) : L, ref: A ? void 0 : B });
}), function(e2, t2) {
  return true;
});

// app/routes/_index.tsx
var import_jsx_dev_runtime2 = __toESM(require_jsx_dev_runtime(), 1);
if (!window.$RefreshReg$ || !window.$RefreshSig$ || !window.$RefreshRuntime$) {
  console.warn("remix:hmr: React Fast Refresh only works when the Remix compiler is running in development mode.");
} else {
  prevRefreshReg = window.$RefreshReg$;
  prevRefreshSig = window.$RefreshSig$;
  window.$RefreshReg$ = (type, id) => {
    window.$RefreshRuntime$.register(type, '"app/routes/_index.tsx"' + id);
  };
  window.$RefreshSig$ = window.$RefreshRuntime$.createSignatureFunctionForTransform;
}
var prevRefreshReg;
var prevRefreshSig;
if (import.meta) {
  import.meta.hot = createHotContext(
    //@ts-expect-error
    "app/routes/_index.tsx"
  );
  import.meta.hot.lastModified = "1738662837906.6753";
}
function Index() {
  const images = ["/images/home/hero-01.jpg", "/images/home/hero-02.jpg", "/images/home/hero-03.jpg"];
  return /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("main", { children: [
    /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("section", { className: "body-font", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("div", { className: "min-h-screen bg-background flex flex-col items-center justify-center", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(MaxWidthWrapper, { children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("div", { className: "w-full text-center mb-8", children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("h1", { className: "text-5xl font-bold mb-4 text-foreground", children: "Welcome to" }, void 0, false, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 36,
          columnNumber: 15
        }, this),
        /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(m, { sequence: ["AI for Model-Driven Engineering!", 5e3, "", 500, "AI4MDE!", 5e3, "", 500], wrapper: "h1", speed: 50, className: "text-5xl font-bold text-accent", repeat: Infinity }, void 0, false, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 37,
          columnNumber: 15
        }, this)
      ] }, void 0, true, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 35,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Carousel, { opts: {
        align: "start",
        loop: true
      }, className: "w-full max-w-5xl mx-auto mb-8", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(CarouselContent, { children: images.map((image, index) => /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(CarouselItem, { children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("div", { className: "relative aspect-[16/9] w-full", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("img", { src: image, alt: `Hero image ${index + 1}`, className: "rounded-lg shadow-md object-cover w-full h-full" }, void 0, false, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 48,
        columnNumber: 23
      }, this) }, void 0, false, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 47,
        columnNumber: 21
      }, this) }, index, false, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 46,
        columnNumber: 47
      }, this)) }, void 0, false, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 45,
        columnNumber: 15
      }, this) }, void 0, false, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 41,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("div", { className: "w-full md:w-2/3 text-center mx-auto mb-12", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("p", { className: "text-xl leading-relaxed text-muted-foreground", children: "Artifacial Intelligence for Model-Driven Engineering in short AI4MDE is an initiative from Leiden University. Model-Driven Engineering (MDE) is a software development methodology that emphasizes the use of domain-specific models as primary artifacts throughout the development lifecycle. This project uses AI, more specific Large Language Models (LLMs) to conduct interviews with stakeholders and transforms these to requirements, models and documents required in the software development lifecycle. The aim of this project is to support Business Analysts and Architects speed up the software requirements engineering process." }, void 0, false, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 56,
        columnNumber: 15
      }, this) }, void 0, false, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 55,
        columnNumber: 13
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("div", { className: "text-center space-x-4", children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Button, { asChild: true, className: "bg-accent hover:bg-accent/90 text-accent-foreground", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Link, { to: "/guide", children: "Get Started" }, void 0, false, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 65,
          columnNumber: 17
        }, this) }, void 0, false, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 64,
          columnNumber: 15
        }, this),
        /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Button, { asChild: true, variant: "outline", className: "border-accent hover:bg-accent hover:text-accent-foreground", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Link, { to: "/contact", children: "Contact Us" }, void 0, false, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 68,
          columnNumber: 17
        }, this) }, void 0, false, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 67,
          columnNumber: 15
        }, this)
      ] }, void 0, true, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 63,
        columnNumber: 13
      }, this)
    ] }, void 0, true, {
      fileName: "app/routes/_index.tsx",
      lineNumber: 33,
      columnNumber: 11
    }, this) }, void 0, false, {
      fileName: "app/routes/_index.tsx",
      lineNumber: 32,
      columnNumber: 9
    }, this) }, void 0, false, {
      fileName: "app/routes/_index.tsx",
      lineNumber: 31,
      columnNumber: 7
    }, this),
    /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("section", { className: "bg-card", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("div", { className: "container px-5 py-24 mx-auto", children: [
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("h2", { className: "text-4xl pb-8 mb-4 font-bold text-center text-card-foreground", children: "Features" }, void 0, false, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 77,
        columnNumber: 11
      }, this),
      /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("div", { className: "flex flex-wrap -m-4", children: [
        /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("div", { className: "p-4 lg:w-1/3", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Card, { className: "h-full bg-background text-foreground", children: [
          /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(CardHeader, { children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(CardTitle, { className: "tracking-widest text-xs font-medium mb-1 text-muted-foreground", children: "CHATBOT DRIVEN BY LLM" }, void 0, false, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 85,
            columnNumber: 19
          }, this) }, void 0, false, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 84,
            columnNumber: 17
          }, this),
          /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(CardContent, { children: [
            /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("h1", { className: "title-font sm:text-2xl text-xl font-medium mb-3", children: "Intelligent Interaction" }, void 0, false, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 90,
              columnNumber: 19
            }, this),
            /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("p", { className: "leading-relaxed mb-3 text-muted-foreground", children: "Discover our modularly designed AI-driven chatbot for engaging with end users. The chatbot makes use of AI agents, each of which is responsible for a specific task or function. This makes it relatively simple to adjust existing functionalities or add new ones. functions relatively simple. Natural language conversations guide the user through a predetermined procedure. Using natural language dialogue, it guides users through a predetermined procedure." }, void 0, false, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 93,
              columnNumber: 19
            }, this)
          ] }, void 0, true, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 89,
            columnNumber: 17
          }, this),
          /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(CardFooter, { className: "flex justify-center", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Link, { to: "/guide", className: "inline-flex items-center text-accent hover:text-accent/90", children: [
            "Learn More",
            /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("svg", { className: "w-4 h-4 ml-2", viewBox: "0 0 24 24", stroke: "currentColor", strokeWidth: "2", fill: "none", strokeLinecap: "round", strokeLinejoin: "round", children: [
              /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("path", { d: "M5 12h14" }, void 0, false, {
                fileName: "app/routes/_index.tsx",
                lineNumber: 101,
                columnNumber: 23
              }, this),
              /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("path", { d: "M12 5l7 7-7 7" }, void 0, false, {
                fileName: "app/routes/_index.tsx",
                lineNumber: 102,
                columnNumber: 23
              }, this)
            ] }, void 0, true, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 100,
              columnNumber: 21
            }, this)
          ] }, void 0, true, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 98,
            columnNumber: 19
          }, this) }, void 0, false, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 97,
            columnNumber: 17
          }, this)
        ] }, void 0, true, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 83,
          columnNumber: 15
        }, this) }, void 0, false, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 82,
          columnNumber: 13
        }, this),
        /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("div", { className: "p-4 lg:w-1/3", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Card, { className: "h-full bg-background text-foreground", children: [
          /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(CardHeader, { children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(CardTitle, { className: "tracking-widest text-xs font-medium mb-1 text-muted-foreground", children: "SOFTWARE REQUIREMENTS SPECIFICATION" }, void 0, false, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 112,
            columnNumber: 19
          }, this) }, void 0, false, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 111,
            columnNumber: 17
          }, this),
          /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(CardContent, { children: [
            /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("h1", { className: "title-font sm:text-2xl text-xl font-medium mb-3", children: "Automated SRS Generation" }, void 0, false, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 117,
              columnNumber: 19
            }, this),
            /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("p", { className: "leading-relaxed mb-3 text-muted-foreground", children: "Transform natural language conversations into comprehensive Software Requirements Specification documents. Our AI-powered system gathers and analyses user requirements through an interview and then automatically generates UML models. In conclusion, the system generates a software requirements specification (SRS) document that is compliant with the standards established by the IEEE." }, void 0, false, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 120,
              columnNumber: 19
            }, this)
          ] }, void 0, true, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 116,
            columnNumber: 17
          }, this),
          /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(CardFooter, { className: "flex justify-center", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Link, { to: "/guide", className: "inline-flex items-center text-accent hover:text-accent/90", children: [
            "Learn More",
            /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("svg", { className: "w-4 h-4 ml-2", viewBox: "0 0 24 24", stroke: "currentColor", strokeWidth: "2", fill: "none", strokeLinecap: "round", strokeLinejoin: "round", children: [
              /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("path", { d: "M5 12h14" }, void 0, false, {
                fileName: "app/routes/_index.tsx",
                lineNumber: 128,
                columnNumber: 23
              }, this),
              /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("path", { d: "M12 5l7 7-7 7" }, void 0, false, {
                fileName: "app/routes/_index.tsx",
                lineNumber: 129,
                columnNumber: 23
              }, this)
            ] }, void 0, true, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 127,
              columnNumber: 21
            }, this)
          ] }, void 0, true, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 125,
            columnNumber: 19
          }, this) }, void 0, false, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 124,
            columnNumber: 17
          }, this)
        ] }, void 0, true, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 110,
          columnNumber: 15
        }, this) }, void 0, false, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 109,
          columnNumber: 13
        }, this),
        /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("div", { className: "p-4 lg:w-1/3", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Card, { className: "h-full bg-background text-foreground", children: [
          /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(CardHeader, { children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(CardTitle, { className: "tracking-widest text-xs font-medium mb-1 text-muted-foreground", children: "UML DIAGRAMS GENERATION" }, void 0, false, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 139,
            columnNumber: 19
          }, this) }, void 0, false, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 138,
            columnNumber: 17
          }, this),
          /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(CardContent, { children: [
            /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("h1", { className: "title-font sm:text-2xl text-xl font-medium mb-3", children: "Automated Design Visualization" }, void 0, false, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 144,
              columnNumber: 19
            }, this),
            /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("p", { className: "leading-relaxed mb-3 text-muted-foreground", children: "Convert natural language descriptions into precise UML diagrams automatically. Our AI system generates various diagram types, including class, sequence, and use case diagrams, providing clear visual representations of your software architecture and system behaviour while maintaining UML standards and best practices. Finaly the UML diagrams can be modified in the Studio app." }, void 0, false, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 147,
              columnNumber: 19
            }, this)
          ] }, void 0, true, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 143,
            columnNumber: 17
          }, this),
          /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(CardFooter, { className: "flex justify-center", children: /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)(Link, { to: "/guide", className: "inline-flex items-center text-accent hover:text-accent/90", children: [
            "Learn More",
            /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("svg", { className: "w-4 h-4 ml-2", viewBox: "0 0 24 24", stroke: "currentColor", strokeWidth: "2", fill: "none", strokeLinecap: "round", strokeLinejoin: "round", children: [
              /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("path", { d: "M5 12h14" }, void 0, false, {
                fileName: "app/routes/_index.tsx",
                lineNumber: 155,
                columnNumber: 23
              }, this),
              /* @__PURE__ */ (0, import_jsx_dev_runtime2.jsxDEV)("path", { d: "M12 5l7 7-7 7" }, void 0, false, {
                fileName: "app/routes/_index.tsx",
                lineNumber: 156,
                columnNumber: 23
              }, this)
            ] }, void 0, true, {
              fileName: "app/routes/_index.tsx",
              lineNumber: 154,
              columnNumber: 21
            }, this)
          ] }, void 0, true, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 152,
            columnNumber: 19
          }, this) }, void 0, false, {
            fileName: "app/routes/_index.tsx",
            lineNumber: 151,
            columnNumber: 17
          }, this)
        ] }, void 0, true, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 137,
          columnNumber: 15
        }, this) }, void 0, false, {
          fileName: "app/routes/_index.tsx",
          lineNumber: 136,
          columnNumber: 13
        }, this)
      ] }, void 0, true, {
        fileName: "app/routes/_index.tsx",
        lineNumber: 80,
        columnNumber: 11
      }, this)
    ] }, void 0, true, {
      fileName: "app/routes/_index.tsx",
      lineNumber: 76,
      columnNumber: 9
    }, this) }, void 0, false, {
      fileName: "app/routes/_index.tsx",
      lineNumber: 75,
      columnNumber: 7
    }, this)
  ] }, void 0, true, {
    fileName: "app/routes/_index.tsx",
    lineNumber: 30,
    columnNumber: 10
  }, this);
}
_c7 = Index;
var _c7;
$RefreshReg$(_c7, "Index");
window.$RefreshReg$ = prevRefreshReg;
window.$RefreshSig$ = prevRefreshSig;
export {
  Index as default
};
//# sourceMappingURL=/build/routes/_index-KBADKMCX.js.map
